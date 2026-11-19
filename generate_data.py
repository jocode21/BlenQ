"""BlenQ — dataset generator.

Builds ~16,000 English prompt -> Blender Python examples from
templates, one fixed world of 15 objects. Every example is made
from an object definition in objects.py, a size and a colour, so
every script in the dataset is a real script that runs in Blender
(see validate.py and tools/blender_job.py for the checks).

Splits (seed 42): train 12,800 / val 1,600 / test 1,600.
Vocab is built from every token in the prompts and scripts, plus
the four special tokens, and saved as data/vocab.json.

Run:  python generate_data.py
"""
import json
import os
import random
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from model import PAD, UNK, BOS, EOS, tokenize  # noqa: E402
from objects import OBJECTS, SIZES, build_script  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
TOTAL = 16000
TRAIN_N, VAL_N = 12800, 1600

# Prompt phrasing. Prompts are built combinatorially — openers,
# verbs, closers, size words and colour words combine freely — so
# the 16,000 examples are genuinely varied instead of the same 27
# sentences repeated. A template without a size or colour word
# still means the default size and colour for that object.
PREFIX_OPENERS = [
    "", "please ", "hey ", "could you ", "can you ", "in blender ",
    "in blender, ", "hey blenq, ", "please can you ",
    "could you please ",
]
CLAUSE_OPENERS = ["i want ", "i need ", "i'd like ", "i would like "]
VERBS = ["make", "build", "create", "generate", "model", "draw",
         "show me", "give me"]
CLOSERS = ["", " for me", " please", " in blender", " as a 3d model",
           " now"]
SIZE_WORDS = {
    "small": ["small", "tiny", "little"],
    "medium": ["medium", "normal"],
    "large": ["large", "big", "huge"],
}
COLOUR_WORDS = {
    "red": ["red"], "blue": ["blue"], "green": ["green"],
    "yellow": ["yellow"], "white": ["white"], "black": ["black"],
    "gold": ["gold", "golden"], "silver": ["silver", "grey", "gray"],
    "grey": ["grey", "gray", "silver"],
    "brown": ["brown"], "purple": ["purple"], "orange": ["orange"],
    "pink": ["pink"],
}


def _prompt(rng, obj_name):
    obj = OBJECTS[obj_name]
    name = rng.choice(obj["synonyms"])
    size = rng.choice(list(SIZES))
    colour = rng.choice(list(obj["colours"]))
    # Size and colour words appear in about 3 out of 5 prompts;
    # when a word is left out the default size/colour is meant.
    size_word = rng.choice(SIZE_WORDS[size]) if rng.random() < 0.6 else None
    colour_word = rng.choice(COLOUR_WORDS[colour]) if rng.random() < 0.6 else None
    if size_word is None:
        size = "medium"
    if colour_word is None:
        colour = next(iter(obj["colours"]))
    parts = " ".join(w for w in (size_word, colour_word, name) if w)
    closer = rng.choice(CLOSERS)
    if rng.random() < 0.3:
        text = rng.choice(CLAUSE_OPENERS) + "a " + parts + closer
    else:
        text = (rng.choice(PREFIX_OPENERS) + rng.choice(VERBS)
                + " a " + parts + closer)
    return text, size, colour


def build_dataset(seed=42):
    rng = random.Random(seed)
    base = TOTAL // len(OBJECTS)
    extra = TOTAL - base * len(OBJECTS)  # 10: first 10 objects get one more
    rows = []
    seen = set()
    for i, obj_name in enumerate(OBJECTS):
        per_object = base + (1 if i < extra else 0)
        made = 0
        guard = 0
        while made < per_object and guard < per_object * 40:
            guard += 1
            prompt, size, colour = _prompt(rng, obj_name)
            script = build_script(obj_name, size, colour)
            key = (prompt, script)
            if key in seen:
                continue
            seen.add(key)
            rows.append({
                "input": prompt,
                "script": script,
                "object": obj_name,
                "size": size,
                "colour": colour,
            })
            made += 1
    rng.shuffle(rows)
    return rows


def build_vocab(rows):
    vocab = {PAD: 0, UNK: 1, BOS: 2, EOS: 3}
    toks = set()
    for r in rows:
        toks.update(tokenize(r["input"].lower()))
        toks.update(tokenize(r["script"]))
    for t in sorted(toks):
        if t not in vocab:
            vocab[t] = len(vocab)
    return vocab


def main():
    os.makedirs(DATA, exist_ok=True)
    rows = build_dataset()
    assert len(rows) == TOTAL, f"expected {TOTAL}, got {len(rows)}"
    vocab = build_vocab(rows)
    with open(os.path.join(DATA, "dataset.jsonl"), "w") as f:
        for r in rows:
            f.write(json.dumps(r) + "\n")
    with open(os.path.join(DATA, "train.jsonl"), "w") as f:
        for r in rows[:TRAIN_N]:
            f.write(json.dumps(r) + "\n")
    with open(os.path.join(DATA, "val.jsonl"), "w") as f:
        for r in rows[TRAIN_N:TRAIN_N + VAL_N]:
            f.write(json.dumps(r) + "\n")
    with open(os.path.join(DATA, "test.jsonl"), "w") as f:
        for r in rows[TRAIN_N + VAL_N:]:
            f.write(json.dumps(r) + "\n")
    with open(os.path.join(DATA, "vocab.json"), "w") as f:
        json.dump(vocab, f, indent=1)
    # Token lengths, so the model shape can be checked at a glance.
    lens = [len(tokenize(r["script"])) for r in rows]
    print(f"examples: {len(rows)}  train {TRAIN_N}  val {VAL_N}  "
          f"test {len(rows) - TRAIN_N - VAL_N}")
    print(f"vocab: {len(vocab)}")
    print(f"script tokens: min {min(lens)}  max {max(lens)}  "
          f"mean {sum(lens) / len(lens):.1f}")
    print("per object:")
    from collections import Counter
    for name, n in sorted(Counter(r["object"] for r in rows).items()):
        print(f"  {name}: {n}")


if __name__ == "__main__":
    main()
