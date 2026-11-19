#!/usr/bin/env python3
"""BlenQ — tiny transformer that turns plain English into Blender Python.

Usage:
    python main.py generate "a small red sword"     # print a script
    python main.py render "a small red sword"       # generate + render to PNG
    python main.py objects                          # list the 15 objects
    python main.py serve                            # start the web UI

Training and data live in their own scripts:
    python generate_data.py   # build the dataset (~16,000 examples)
    python train.py --full    # full 30-epoch training (GPU required)
    python train.py           # small smoke run (CPU is fine)
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from blender_tools import render_script  # noqa: E402
from model import generate, get_model  # noqa: E402
from objects import OBJECTS  # noqa: E402


def _generate(prompt):
    """Generate a script with the trained model.

    Returns (script, info). The model must exist first — run the full
    training on a GPU machine, or the smoke run, to create data/model.pt.
    """
    try:
        model, vocab = get_model(device="cpu")
    except FileNotFoundError as e:
        return None, {"error": str(e)}
    try:
        script = generate(model, vocab, prompt, device="cpu")
    except Exception as e:
        return None, {"error": f"The model failed to answer: {e}"}
    return script, None


def cmd_generate(args):
    script, info = _generate(args.prompt)
    if script is None:
        print("BlenQ could not understand that prompt.")
        print("Try one of the 15 objects: " + ", ".join(sorted(OBJECTS)))
        if info:
            print("Reason:", info.get("error", "unknown"))
        return 1
    print(script)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(script)
        print(f"\nSaved to {args.out}")
    return 0


def cmd_render(args):
    script, info = _generate(args.prompt)
    if script is None:
        print("BlenQ could not understand that prompt.")
        return 1
    out = args.out or "blenq_render.png"
    ok, err = render_script(script, out)
    if ok:
        print(f"Rendered to {out}")
        return 0
    print("Render failed:", err)
    return 1


def cmd_objects(_args):
    for name in sorted(OBJECTS):
        spec = OBJECTS[name]
        colours = ", ".join(spec["colours"])
        print(f"{spec['display']:14s} colours: {colours}")
    return 0


def cmd_serve(_args):
    import app

    app.app.run(host="127.0.0.1", port=5000, debug=False)


def main():
    parser = argparse.ArgumentParser(prog="blenq", description="BlenQ — English to Blender Python")
    sub = parser.add_subparsers(dest="command", required=True)

    p_gen = sub.add_parser("generate", help="print a Blender script for a prompt")
    p_gen.add_argument("prompt")
    p_gen.add_argument("--out", help="also save the script to this file")
    p_gen.set_defaults(func=cmd_generate)

    p_render = sub.add_parser("render", help="generate and render a prompt to a PNG")
    p_render.add_argument("prompt")
    p_render.add_argument("--out", default="blenq_render.png")
    p_render.set_defaults(func=cmd_render)

    p_obj = sub.add_parser("objects", help="list the 15 objects BlenQ knows")
    p_obj.set_defaults(func=cmd_objects)

    p_serve = sub.add_parser("serve", help="start the web UI on http://127.0.0.1:5000")
    p_serve.set_defaults(func=cmd_serve)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
