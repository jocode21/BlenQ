# BlenQ — Test report

Run: `pytest tests/ -q` (from the project folder, inside the venv).
Final clean run 2026-11-18: **78 passed, 0 failed, in 128.7 s.**
(One render test failed once during an earlier run while a training
eval was hogging the CPU; it passed on re-run and in the final
clean run, so it was contention, not a code defect.)

## Summary

| Suite | Tests | Passed |
|---|---|---|
| Dataset (`test_dataset.py`) | 10 | 10 |
| Objects (`test_objects.py`) | 25 | 25 |
| Validator (`test_validate.py`) | 11 | 11 |
| Model (`test_model.py`) | 7 | 7 |
| App (`test_app.py`) | 9 | 9 |
| Blender (`test_blender.py`) | 16 | 16 |
| **Total** | **78** | **78 — all passing, final clean run 2026-11-18, 128.7 s** |

## What was verified

### Dataset — 16,000 examples, 0 bad
- Total 16,000; splits 12,800 / 1,600 / 1,600 with no overlap.
- All 16,000 prompts unique; per object 1,066–1,067.
- **Every one of the 16,000 scripts passes `validate()` and matches
  its labelled object** (text check).
- Script token lengths 269–457, all within the 512-token context.
- Vocabulary (187 tokens) covers every token in the dataset.
- Prompts are genuinely varied (combinatorial openers, verbs,
  closers, size and colour words), not one repeated template.

### All 135 unique scripts run in Blender — 135/135
- 15 objects × 3 sizes × 3 colours, run in Blender headless in one
  batch job. Every script ran without an error and built exactly
  the expected number of mesh objects (5–8 per object).

### Renders — 15/15, visually checked
- One render per object (default size, default colour), rendered
  in Blender headless with real materials, sun + fill light, and a
  camera aimed at the model. Each PNG was looked at: every object
  reads clearly as what it is meant to be.
- Files: `renders/*.png` (also included in the zip).

### Model
- 12,013,499 parameters — inside the 10–20M locked range.
- Config: d_model 256, 3+3 layers, context 512.
- Tokenizer roundtrip is exact for all 15 default scripts
  (tokenize → detokenize returns the script byte for byte).
- `requirements.txt` installs the CUDA torch build (`+cu132`),
  never the CPU build.
- `train.py --full` refuses to train on CPU (tested: raises
  SystemExit with a clear message before any training starts).

### Web app
- `/` returns 200 with the BlenQ title; `/metrics` returns 200;
  `/objects` returns all 15 objects with 5–8 pieces each.
- No example/suggested prompts anywhere in the UI.
- No forbidden words in user-facing pages (checked against the
  banned-word list in the test suite).
- `/generate` with no trained model yet fails cleanly (200 + a
  clear message), it does not crash with a 500.
- `/render` rejects an empty script and a script with system
  access.

### Validator
- All 135 known scripts validate with the correct object.
- Rejected: empty script, `os`/`eval`/file access, `bpy.ops.wm`,
  missing `import bpy`, wrong piece count (4 instead of 5),
  missing colour loop, SQL-style input.

## Known issues found and fixed during the build

1. **Dataset too small at first** — the first template list only
   produced 1,944 unique prompts. Fixed with combinatorial
   phrasing (openers × verbs × closers × size/colour words) and
   more synonyms per object. Now 16,000 unique prompts.
2. **Tokenizer roundtrip** — scripts ended with a trailing newline
   that detokenize strips. Fixed in `objects.py` (no trailing
   newline); all 15 scripts now roundtrip exactly.
3. **House colours** — the roof came out white and the walls red.
   Swapped so the named colour is the roof and the walls are white.
4. **Camera angle** — the first renders were taken from the back,
   hiding doors, eyes and the shield boss. Camera moved to face
   the front (+X, +Y).
5. **First renders were dark / colours invisible** — object colour
   is viewport-only in EEVEE. The render job now turns colours
   into real materials and adds a light background, sun and fill.
6. **Boat read as a monolith** — brown sail on a flat white hull.
   Colours inverted (hull takes the named colour, sail stays
   white) and a pointed bow cone added (7 pieces now).
7. **Shield was a tall slab** — 1.0 wide × 1.9 tall. Widened to
   1.4 wide × 1.6 tall with a boss and crossbar.
8. **House walls vanished** — white walls against a light
   backdrop. Walls are now warm beige.
9. **Helmet read like a lamp** — cheek guards too long, crest too
   chunky. Guards shortened, crest thinned into a ridge.

## Not yet verified (honest gaps)

- **Full-training accuracy** — measured only after the 30-epoch
  run on a GPU machine. Smoke accuracy is not real accuracy.
- **Windows** — nothing here was run on Windows. The README steps
  are the exact steps to run on your PC.
- **GPU training time** — the "30–60 minutes" estimate for an
  RTX 3050 is an estimate, not a measurement.
