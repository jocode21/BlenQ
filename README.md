# BlenQ

**BlenQ turns plain English into Blender Python.** Type something like
"make a small red sword" and BlenQ writes a normal, readable Blender
script (`.py`). Run the script in Blender and it builds the model —
save it as a `.blend`, render a `.png`. No pretrained model, no API,
no internet: a tiny transformer trained from scratch, free, on your
own computer.

## Full-training result (measured 2026-11-19, on Joel's PC)

| | |
|---|---|
| **Exact match** | **100% (200/200)** on the full-run eval — beats the 80–90% target |
| **Training** | 30/30 epochs, device=cuda, RTX 3050, ~80 minutes (about 159 s per epoch) |
| **Loss** | 1.7121 → 0.1901 → 0.0702 → 0.0379 → 0.0226 by epoch 5 (final loss was not recorded) |
| **Render** | 8.8 s for a car on Blender 5.2, end to end in the app |

Runnable-in-Blender and correct-shape-count were **not measured** by
the full-run eval (both came back null) — they are not claimed here.
See TRAINING_LOG.md for the full numbers.

## Known issues (honest)

- **Car wheels are squished in the trained model.** The training
  data had the wheel scale wrong (`(0.2, 0.08, 0.2)` instead of
  `(0.2, 0.2, 0.08)`), so the 100% model still generates squished
  wheels. The data is fixed in `objects.py` now, but the model has
  **not been retrained** with the fix yet — a retrain (~80 min) is
  needed before the model itself writes round wheels. A fixed car
  render made from the corrected script is in `renders/car.png`.
- **Blender 5.2 render fix.** Blender 5.0+ renamed the render
  engine from `BLENDER_EEVEE_NEXT` back to `BLENDER_EEVEE`; the
  original `tools/blender_job.py` only tried the old name and
  rendering failed on Blender 5.2. It now tries `BLENDER_EEVEE`
  first and falls back to `BLENDER_EEVEE_NEXT`.

## What it does

| | |
|---|---|
| **Input** | Plain English, free wording — "build a big blue house", "i want a tiny gold crown", "please make a robot" |
| **Output** | A readable Blender Python script (`.py`), 5–8 pieces per model |
| **Objects** | 15 fixed objects: Sword, Shield, Axe, War hammer, Dagger, Helmet, Crown, Rocket, Car, Boat, Castle tower, House, Tree, Robot, Treasure chest |
| **Sizes** | small, medium, large (also "tiny", "little", "big", "huge") |
| **Colours** | 3 per object (for example a car can be red, blue or black) |
| **Model** | Tiny transformer, 12,013,499 parameters, trained from scratch on 16,000 examples |
| **Cost** | Free. Runs on your own computer. |

## What it does NOT do (honest limits)

- **Simple, blocky models only.** No textures, no fine detail, nothing
  like a realistic gun or a detailed character. Each model is 5–8
  simple shapes (cubes, cylinders, spheres, cones) arranged into an
  object. If you want detail, open the generated `.py` in Blender and
  edit it — it is normal readable code.
- **15 objects only.** Anything outside those 15 will not work
  reliably. The model only knows the world it was trained on.
- **Full training is done — see the result box above.** The
  numbers in TRAINING_LOG.md cover both the smoke run and the
  real full run (100% exact match, 200/200). Runnable-in-Blender
  and correct-shape-count were not measured by the full-run eval,
  so they are not claimed.
- **Windows / GPU validation is done.** Full training ran on
  Windows on an RTX 3050 (CUDA, ~80 min) and the app renders in
  Blender 5.2 on the same machine.

## How it works

```
English prompt  →  tiny transformer  →  Blender Python (.py)
                                            ↓
                                   Blender (headless or the app)
                                            ↓
                                   3D model → .blend / .png
```

1. `generate_data.py` builds 16,000 English → script examples from
   templates (12,800 train / 1,600 val / 1,600 test, seed 42).
2. `train.py` trains a 6-layer transformer (d_model 256, context
   512 tokens) from scratch. Context is 512, not 256: a readable
   Blender script with 5–8 pieces measures 269–457 tokens, so 256
   cannot hold it.
3. `app.py` is the web UI: type English, get the script, copy it,
   download the `.py`, or press **Render in Blender** and see a
   picture of the model it built.
4. `validate.py` checks a script before it runs: it must start with
   `import bpy`, use only the Blender API, contain no file or system
   access, have 5–8 pieces, and fit in 512 tokens.

## Quick start — on your PC (Windows, RTX 3050)

### Step 0 — check the GPU torch build FIRST (do not skip this)

A previous project shipped a CPU-only torch by mistake and trained
on the CPU without anyone noticing. BlenQ refuses to make that
mistake: `train.py --full` stops at once if it cannot see a GPU.

```bat
python -c "import torch; print(torch.__version__); print(torch.cuda.is_available())"
```

It must print a version ending in `+cu132`, then `True`. Then check
the GPU name:

```bat
python -c "import torch; print(torch.cuda.get_device_name(0))"
```

That must print your RTX 3050. If it prints `False` or a CPU-only
version, uninstall torch and install the CUDA build first:

```bat
pip uninstall torch -y
pip install -r requirements.txt
```

### Step 1 — install

```bat
cd BlenQ_v1
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### Step 2 — build the dataset

```bat
python generate_data.py
```

Makes `data/dataset.jsonl` (16,000 examples), `train.jsonl`,
`val.jsonl`, `test.jsonl` and `vocab.json`. Takes a few seconds.

### Step 3 — full training (30 epochs, GPU)

```bat
python train.py --full
```

About 80 minutes on an RTX 3050 (measured 2026-11-19: about
159 s per epoch × 30 epochs). It saves `data/model.pt` and writes
`data/training_metrics.json` with exact match, runnable-in-Blender
and correct-shape-count, measured on 200 validation rows. On the
2026-11-19 full run, exact match was **100% (200/200)**;
runnable-in-Blender and correct-shape-count came back null
(not measured by the eval) and are not claimed. The model
file is **not** included in this repo and must never be pushed to a
public repo — it is created by training.

### Step 4 — use it

```bat
python app.py
```

Open http://127.0.0.1:5000 in your browser. Type English, get the
script, download the `.py`, or render it. Or from the command line:

```bat
python main.py generate "a small red sword" --out sword.py
python main.py render "a small red sword" --out sword.png
python main.py objects
```

Then open `sword.py` in Blender: Scripting workspace → Open →
Run Script. Save as `.blend`, render as `.png`.

## Smoke run (quick pipeline check, no GPU needed)

```bat
python train.py --smoke
```

2,000 examples, 3 epochs, a few minutes on CPU. Loss must go down
and `data/model.pt` must be saved. Accuracy after a smoke run is
**low by design** — it only proves the pipeline works end to end.
Never present smoke accuracy as the model's real accuracy.

## Project layout

```
BlenQ_v1/
├── app.py               web UI (Flask, http://127.0.0.1:5000)
├── main.py              command line: generate / render / objects / serve
├── objects.py           the 15 objects: pieces, sizes, colours, scripts
├── model.py             tiny transformer + tokenizer (newlines kept)
├── train.py             training + evaluation (Blender-checked)
├── generate_data.py     builds the 16,000-example dataset
├── validate.py          script safety + shape checks
├── blender_tools.py     runs scripts in Blender headless, renders PNGs
├── tools/blender_job.py the script that runs INSIDE Blender
├── templates/           pretty dark UI (index.html, metrics.html)
├── tests/               pytest suite (see TEST_REPORT.md)
├── data/                dataset + vocab (model.pt is created by training)
├── renders/             one rendered picture per object (15 PNGs)
├── requirements.txt     CUDA torch build — never the CPU build
├── README.md            this file
├── TRAINING_LOG.md      smoke vs full training numbers
└── TEST_REPORT.md       what was tested, and the measured results
```

## Blender

BlenQ needs Blender only to **render** and to **verify** scripts.
Generating a script needs no Blender at all. If Blender is not
found, the app still generates scripts — rendering is disabled and
the app tells you so. Set the Blender executable with the
`BLENQ_BLENDER` environment variable, or open the downloaded `.py`
in Blender yourself. Blender 4.2 or newer works. On Blender 5.0+
the render engine is called `BLENDER_EEVEE` (not
`BLENDER_EEVEE_NEXT` as in 4.2–4.4); `tools/blender_job.py` tries
both names, so rendering works on 4.2 and on 5.2.

## The 15 objects

| Object | Pieces | Colours |
|---|---|---|
| Sword | 6 | silver, gold, black |
| Shield | 6 | red, blue, green |
| Axe | 5 | silver, gold, black |
| War hammer | 5 | grey, gold, black |
| Dagger | 5 | silver, gold, black |
| Helmet | 6 | silver, gold, black |
| Crown | 6 | gold, silver, red |
| Rocket | 8 | white, red, blue |
| Car | 8 | red, blue, yellow |
| Boat | 7 | brown, red, blue |
| Castle tower | 8 | grey, brown, white |
| House | 6 | red, blue, yellow |
| Tree | 5 | green, orange, yellow |
| Robot | 8 | grey, blue, red |
| Treasure chest | 6 | brown, red, black |

## Tests

```bat
pytest tests/ -q
```

See TEST_REPORT.md for the full list and the measured results.
The suite checks the dataset, the objects, the validator, the model
shape, the app endpoints, and — most importantly — it runs every
default script and one render in Blender headless.

## License

Built from scratch for learning and portfolio use. The model
weights you train are yours. Blender is a separate project under
its own license.
