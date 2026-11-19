"""BlenQ — training script (from scratch, no pretrained weights).

  Full training (Joel's PC, RTX 3050):
      python train.py --full
      -> 16,000 examples, 30 epochs, batch 16, AdamW lr 3e-4, CUDA.
         --full REQUIRES a CUDA torch build and refuses to train on
         CPU: if torch.cuda.is_available() is False it stops at once
         with a clear error instead of silently training on CPU.
         Check first with:
           python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
         That must print True and the RTX 3050 name before training.
         Expected time on an RTX 3050: roughly 30-60 minutes
         (not measured yet — this machine has no GPU).

  Smoke training (quick pipeline check, CPU is fine here):
      python train.py --smoke
      -> 2,000 examples, 3 epochs, batch 16, CPU. A few minutes.
         Loss must go down and model.pt must be saved. Accuracy after
         a smoke run is LOW by design and is reported honestly in
         data/training_metrics.json — never present it as
         full-training accuracy.

  Evaluate an existing checkpoint:
      python train.py --eval-only [--eval-limit 200]

Outputs: data/model.pt, data/training_metrics.json
"""
import argparse
import json
import os
import sys
import time

import torch
import torch.nn as nn
from torch.utils.data import DataLoader, Dataset

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from blender_tools import run_scripts  # noqa: E402
from model import (  # noqa: E402
    BOS, EOS, PAD, build_model, count_parameters, decode, encode,
    generate, load_vocab, save_checkpoint,
)
from objects import piece_count  # noqa: E402
from validate import validate  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")


def load_jsonl(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]


class ScriptDataset(Dataset):
    def __init__(self, rows, vocab):
        self.rows = rows
        self.vocab = vocab

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, i):
        r = self.rows[i]
        src = encode(r["input"], self.vocab, lowercase=True)
        tgt = encode(r["script"], self.vocab)
        return src, tgt


def collate(batch, vocab):
    pad = vocab[PAD]
    srcs = [torch.tensor(s, dtype=torch.long) for s, _ in batch]
    tgts = [torch.tensor(t, dtype=torch.long) for _, t in batch]
    src_len = max(len(s) for s in srcs)
    tgt_len = max(len(t) for t in tgts) + 1  # +1 for EOS
    src_padded = torch.full((len(batch), src_len), pad, dtype=torch.long)
    # decoder input: BOS + script tokens ; labels: script tokens + EOS
    dec_in = torch.full((len(batch), tgt_len), pad, dtype=torch.long)
    labels = torch.full((len(batch), tgt_len), -100, dtype=torch.long)
    for i, (s, t) in enumerate(zip(srcs, tgts)):
        src_padded[i, : len(s)] = s
        dec_in[i, 0] = vocab[BOS]
        dec_in[i, 1: len(t) + 1] = t
        labels[i, : len(t)] = t
        labels[i, len(t)] = vocab[EOS]
    return src_padded, dec_in, labels


def norm(script):
    return " ".join(script.strip().split())


def evaluate(model, vocab, rows, device, limit=200):
    """Greedy-decode `limit` val rows. Returns a metrics dict.

    Exact match is strict (whitespace-normalised script text).
    Runnable and count-match are measured by actually running the
    generated scripts inside Blender in one batch job: runnable
    means Blender executed the script without an error, count-match
    means it built the expected number of mesh objects. When
    Blender is not available both are reported as None, never as 0.
    """
    model.eval()
    rows = rows[:limit]
    exact = 0
    samples = []
    generated = []
    for r in rows:
        gen = generate(model, vocab, r["input"], device)
        generated.append(gen)
        if norm(gen) == norm(r["script"]):
            exact += 1
        if len(samples) < 5:
            samples.append({"input": r["input"], "expected": r["script"],
                            "generated": gen, "object": r["object"]})
    runnable = None
    runnable_n = 0
    count_ok = None
    count_n = 0
    jobs = []
    for i, (r, gen) in enumerate(zip(rows, generated)):
        ok, _, _ = validate(gen)
        if ok:
            jobs.append({"id": str(i), "object": r["object"],
                         "script": gen, "expected": piece_count(r["object"])})
    if jobs:
        results, err = run_scripts(jobs)
        if err is None and results is not None:
            runnable_n = len(results)
            runnable = sum(1 for x in results if x["error"] is None) / runnable_n
            count_n = runnable_n
            count_ok = sum(1 for x in results if x["ok"]) / count_n
    return {
        "eval_rows": len(rows),
        "exact_match": exact / max(len(rows), 1),
        "exact_match_n": exact,
        "runnable": runnable,
        "runnable_n": runnable_n,
        "count_match": count_ok,
        "count_match_n": count_n,
        "samples": samples,
    }


def train(args):
    device = args.device
    if device == "auto":
        device = "cuda" if torch.cuda.is_available() else "cpu"
    if args.full and device != "cuda":
        raise SystemExit(
            "BlenQ --full refuses to train on CPU.\n"
            "torch.cuda.is_available() is False, so this torch build "
            "cannot see the RTX 3050. Uninstall the CPU torch build "
            "and install a CUDA build first (see README.md, step 3), "
            "then check with:\n"
            '  python -c "import torch; print(torch.__version__); '
            'print(torch.cuda.is_available())"\n'
            "That must print True before training starts."
        )
    print(f"device={device}")
    torch.manual_seed(args.seed)
    vocab = load_vocab(os.path.join(DATA, "vocab.json"))
    train_rows = load_jsonl(os.path.join(DATA, "train.jsonl"))
    val_rows = load_jsonl(os.path.join(DATA, "val.jsonl"))
    if args.limit:
        train_rows = train_rows[: args.limit]
    print(f"device={device} train_rows={len(train_rows)} "
          f"val_rows={len(val_rows)} vocab={len(vocab)}")
    model, cfg = build_model(len(vocab), device=device)
    print(f"parameters: {count_parameters(model):,}")
    ds = ScriptDataset(train_rows, vocab)
    loader = DataLoader(
        ds, batch_size=args.batch_size, shuffle=True,
        collate_fn=lambda b: collate(b, vocab),
    )
    opt = torch.optim.AdamW(model.parameters(), lr=args.lr)
    total_steps = len(loader) * args.epochs
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, total_steps)
    loss_fn = nn.CrossEntropyLoss(ignore_index=-100)
    model.train()
    t0 = time.time()
    history = []
    for ep in range(args.epochs):
        tot, nb = 0.0, 0
        for src, dec_in, labels in loader:
            src, dec_in, labels = (src.to(device), dec_in.to(device),
                                   labels.to(device))
            src_pad = src == vocab[PAD]
            dec_pad = dec_in == vocab[PAD]
            logits = model(src, dec_in, src_pad, dec_pad)
            loss = loss_fn(
                logits.reshape(-1, logits.size(-1)), labels.reshape(-1))
            opt.zero_grad()
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            opt.step()
            sched.step()
            tot += loss.item()
            nb += 1
        avg = tot / max(nb, 1)
        history.append(round(avg, 4))
        print(f"epoch {ep + 1}/{args.epochs} loss={avg:.4f} "
              f"({time.time() - t0:.0f}s)", flush=True)
    save_checkpoint(model, vocab, os.path.join(DATA, "model.pt"))
    print("saved data/model.pt")
    metrics = evaluate(model, vocab, val_rows, device,
                       limit=args.eval_limit)
    metrics.update({
        "mode": "smoke" if args.smoke else "full",
        "epochs": args.epochs,
        "train_examples": len(train_rows),
        "batch_size": args.batch_size,
        "lr": args.lr,
        "device": device,
        "seconds": round(time.time() - t0),
        "loss_history": history,
        "parameters": count_parameters(model),
    })
    with open(os.path.join(DATA, "training_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=1)
    print(json.dumps({k: v for k, v in metrics.items()
                      if k not in ("samples",)}, indent=1))
    return metrics


def main():
    p = argparse.ArgumentParser(description="Train BlenQ from scratch.")
    p.add_argument("--full", action="store_true",
                   help="full training: all 12,800 train rows, 30 epochs, CUDA only")
    p.add_argument("--smoke", action="store_true",
                   help="smoke training: 2,000 rows, 3 epochs, CPU-friendly")
    p.add_argument("--epochs", type=int, default=None)
    p.add_argument("--limit", type=int, default=None,
                   help="max train rows (0 = all)")
    p.add_argument("--batch-size", type=int, default=16)
    p.add_argument("--lr", type=float, default=3e-4)
    p.add_argument("--device", default="auto")
    p.add_argument("--seed", type=int, default=42)
    p.add_argument("--eval-only", action="store_true")
    p.add_argument("--eval-limit", type=int, default=200)
    p.add_argument("--model", default=os.path.join(DATA, "model.pt"))
    args = p.parse_args()
    if args.smoke:
        args.epochs = args.epochs or 3
        args.limit = args.limit or 2000
    elif args.full:
        args.epochs = args.epochs or 30
        args.limit = args.limit or 0
    else:
        args.epochs = args.epochs or 3
        args.limit = args.limit or 0
    if args.eval_only:
        from model import load_checkpoint
        device = args.device
        if device == "auto":
            device = "cuda" if torch.cuda.is_available() else "cpu"
        model, vocab, cfg = load_checkpoint(args.model, device)
        val_rows = load_jsonl(os.path.join(DATA, "val.jsonl"))
        print(json.dumps(evaluate(model, vocab, val_rows, device,
                                  limit=args.eval_limit), indent=1))
        return
    train(args)


if __name__ == "__main__":
    main()
