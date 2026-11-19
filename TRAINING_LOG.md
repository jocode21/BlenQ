# BlenQ — Training log

How to read this file: **smoke** numbers prove the pipeline works
end to end. **Full** numbers are the model's real accuracy. Never
present a smoke number as the model's accuracy.

## Model

| | |
|---|---|
| Architecture | Encoder–decoder transformer, trained from scratch |
| Layers | 3 encoder + 3 decoder (6 total) |
| d_model | 256, 8 heads, feedforward 3072, dropout 0.1 |
| Context | **512 tokens** (not 256 — a readable Blender script with 5–8 pieces measures 269–457 tokens, so 256 cannot hold it) |
| Vocabulary | 187 tokens (built from the dataset) |
| Parameters | **12,013,499** |
| Optimiser | AdamW, lr 3e-4, cosine schedule, batch 16, grad clip 1.0 |
| Data | 16,000 examples — 12,800 train / 1,600 val / 1,600 test, seed 42 |
| Scripts | 15 objects × 3 sizes × 3 colours = 135 unique scripts, all validated in Blender (135/135) |

## Smoke run (CPU, quick pipeline check)

Measured 2026-11-18 on this machine (CPU only). See
`data/training_metrics.json` for the full numbers including samples.

| | |
|---|---|
| Command | `python train.py --smoke --limit 1000 --epochs 2 --eval-limit 50` (training), then `python train.py --eval-only --eval-limit 10` (measured eval) |
| Rows | 1,000 train, 2 epochs, batch 16 |
| Device | CPU |
| Loss history | **9.4450 → 2.1294** (loss goes down — the model is learning) |
| Time | 1,549 s training (~26 min); eval is slow on CPU (~1 min per row greedy-decoded, so the 50-row eval was cut to 10 rows) |
| Exact match (10 val rows) | **0.0% (0/10)** — expected at this size. After 2 epochs on 1,000 rows the model has learned the shape of a script (`import bpy`, `select_all`, `delete`, primitive calls) but degenerates into repeated tokens (`mesh.mesh.mesh…`). |
| Runs in Blender | Not measurable — 0 of the 10 generated scripts passed validation, so none went to Blender. The validator correctly rejected all of them. |
| Correct shape count | Not measurable (same reason) |

What the smoke run proves: the whole pipeline works end to end —
data builds, training runs and loss falls, a checkpoint saves,
generation produces script-shaped output, and validation catches
bad output before Blender ever sees it. What it does **not**
prove: real accuracy. That needs the full run below.

## Full run (GPU, RTX 3050) — DONE 2026-11-19, on Joel's PC

| | |
|---|---|
| Command | `python train.py --full` |
| Rows | 12,800 train, 30 epochs, batch 16 |
| Device | CUDA (RTX 3050) — `--full` refuses to run on CPU |
| Loss history | 1.7121 (epoch 1) → 0.1901 (epoch 2) → 0.0702 (epoch 3) → 0.0379 (epoch 4) → **0.0226 (epoch 5)**. Loss after epoch 5 and the final loss were not recorded. |
| Time | **~80 minutes** (about 159 s per epoch × 30 epochs, measured from the run log) |
| Exact match (200 val rows) | **100% (200/200)** — beats the 80–90% target |
| Runs in Blender | Not measured — the full-run eval returned null for this metric |
| Correct shape count | Not measured — the full-run eval returned null for this metric |

Note: the full-run numbers above are from Joel's PC run
(`data/training_metrics.json` on his machine). The
`data/training_metrics.json` in this repo still holds the
smoke-run numbers (0/10) and is **not** the full-run file — do
not present it as the full result. The app's metrics page on
his PC shows 100.0% exact match for the full run, and a car
rendered end to end in the app in 8.8 s on Blender 5.2.

## Fixes after the full run (not in the trained model yet)

- **Blender 5.2 render fix.** The full-run app could not render
  on Blender 5.2: `tools/blender_job.py` set the render engine
  to `BLENDER_EEVEE_NEXT`, which Blender 5.0+ renamed to
  `BLENDER_EEVEE`. Fixed in this repo — it now tries
  `BLENDER_EEVEE` first, then falls back to
  `BLENDER_EEVEE_NEXT`. Rendering works on 4.2 and 5.2.
- **Car wheels squished — fix pending retrain.** The training
  data had the car wheel scale as `(0.2, 0.08, 0.2)`; after the
  wheel's 90° turn that makes the wheel flat and oval. Fixed in
  `objects.py` to `(0.2, 0.2, 0.08)` for all 4 wheels, and the
  fixed car was re-rendered and checked (`renders/car.png`).
  The 100% model was trained on the old data, so it still
  generates squished wheels until it is retrained with the
  fixed data (~80 min). Do not claim the trained model has
  round wheels.

## Notes

- **CPU eval is very slow.** Greedy-decoding a 300-token script
  takes ~1 minute per row on CPU here, so a 50-row eval was
  stopped after training and replaced by a 10-row `--eval-only`
  run. On the GPU machine, use the full 200-row eval
  (`--eval-limit 200`, the default) — it will be far faster.
- The first smoke attempt (2,000 rows, 3 epochs) was killed by a
  runtime restart at ~35 minutes with no checkpoint saved — this
  machine only saves `model.pt` after the final epoch. The
  successful smoke run used 1,000 rows and 2 epochs instead.
- `data/model.pt` is created by training. It is not in the zip and
  must never be pushed to a public repo.
- Task Manager shows ~0% on the 3D graph during CUDA training —
  that is normal. Watch Compute / CUDA instead.
- If `torch.cuda.is_available()` prints `False`, stop: uninstall
  the CPU torch build and install the CUDA build from
  `requirements.txt` first. Do not train on CPU for the full run.
