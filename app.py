"""BlenQ — web app (Flask).

Run:  python app.py          -> http://127.0.0.1:5000
No server to install, no password, no internet.

Flow:
  1. Type plain English, like "make a sword".
  2. The tiny model writes a Blender Python script (.py).
  3. You can copy it, download it, or press Render in Blender:
     Blender runs the script headlessly and you see a picture of
     the model it built, with the mesh count and render time.
  4. Open the downloaded .py in Blender yourself to keep the
     model as a .blend file.

There is deliberately NO suggested-prompts / example-prompts section
anywhere in the UI. You type free English; the object gallery on
the side shows the 15 objects BlenQ can build, by name only.
"""
import base64
import json
import os
import re
import time

from flask import Flask, jsonify, render_template, request

from blender_tools import find_blender, render_script
from model import generate, get_model
from objects import OBJECTS, piece_count
from validate import validate

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
HISTORY_PATH = os.path.join(DATA, "history.json")

app = Flask(__name__)
app.secret_key = os.environ.get("BLENQ_SECRET", "blenq-dev-only-key")

OBJECT_LIST = [
    {"name": name, "display": OBJECTS[name]["display"],
     "pieces": piece_count(name),
     "colours": list(OBJECTS[name]["colours"])}
    for name in OBJECTS
]


def load_history():
    try:
        with open(HISTORY_PATH) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def save_history(entry):
    hist = load_history()
    hist.insert(0, entry)
    hist = hist[:100]
    os.makedirs(DATA, exist_ok=True)
    with open(HISTORY_PATH, "w") as f:
        json.dump(hist, f, indent=1)


def _metrics():
    path = os.path.join(DATA, "training_metrics.json")
    try:
        with open(path) as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None


@app.route("/")
def index():
    return render_template(
        "index.html", objects=OBJECT_LIST,
        history=load_history()[:10], metrics=_metrics(),
        blender=find_blender(),
    )


@app.route("/objects")
def objects():
    return jsonify(OBJECT_LIST)


@app.route("/metrics")
def metrics():
    m = _metrics()
    return render_template(
        "metrics.html", metrics=m, objects=OBJECT_LIST,
        history=load_history()[:10],
    )


@app.route("/generate", methods=["POST"])
def generate_route():
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or request.form.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"ok": False, "error": "Type a request first."}), 200
    try:
        model, vocab = get_model(device="cpu")
    except FileNotFoundError as e:
        return jsonify({"ok": False, "error": str(e)}), 200
    except Exception as e:  # model file corrupt etc. — never crash
        return jsonify({"ok": False,
                        "error": f"Model could not be loaded: {e}"}), 200
    try:
        script = generate(model, vocab, prompt, device="cpu")
    except Exception as e:
        return jsonify({"ok": False,
                        "error": f"The model failed to answer: {e}"}), 200
    ok, obj, err = validate(script)
    save_history({"prompt": prompt, "script": script, "object": obj,
                  "ok": ok, "error": err})
    if not ok:
        return jsonify({"ok": False, "error": err, "script": script}), 200
    return jsonify({"ok": True, "script": script, "object": obj,
                    "pieces": piece_count(obj) if obj else None}), 200


@app.route("/render", methods=["POST"])
def render_route():
    data = request.get_json(silent=True) or {}
    script = data.get("script") or ""
    if not script.strip():
        return jsonify({"ok": False,
                        "error": "Nothing to render. Generate a script first."}), 200
    ok, obj, err = validate(script)
    if not ok:
        return jsonify({"ok": False, "error": err, "script": script}), 200
    if find_blender() is None:
        return jsonify({
            "ok": False,
            "error": "Blender was not found on this computer. "
                     "Set BLENQ_BLENDER to the Blender executable, "
                     "or open the downloaded .py in Blender yourself.",
            "script": script,
        }), 200
    out_png = os.path.join(DATA, "last_render.png")
    os.makedirs(DATA, exist_ok=True)
    t0 = time.time()
    good, rerr = render_script(script, out_png)
    if not good:
        return jsonify({"ok": False, "error": rerr, "script": script}), 200
    with open(out_png, "rb") as f:
        image = base64.b64encode(f.read()).decode()
    return jsonify({
        "ok": True, "object": obj,
        "pieces": piece_count(obj) if obj else None,
        "seconds": round(time.time() - t0, 1),
        "image": "data:image/png;base64," + image,
        "script": script,
    }), 200


if __name__ == "__main__":
    print("BlenQ running at http://127.0.0.1:5000")
    print("Blender found:", find_blender() or "not found — rendering disabled")
    print("Press Ctrl+C to stop.")
    app.run(host="127.0.0.1", port=5000, debug=False)
