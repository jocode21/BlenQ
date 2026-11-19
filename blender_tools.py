"""BlenQ — run Blender scripts on the host side.

Finds the Blender executable, runs a script inside Blender in
headless mode, and renders a picture of the result. The Blender-side
work lives in tools/blender_job.py, which runs inside Blender.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
JOB = os.path.join(HERE, "tools", "blender_job.py")
BLENDER = os.environ.get(
    "BLENQ_BLENDER",
    os.path.join(
        os.path.expanduser("~"), "workspace", "blender",
        "blender-4.2.0-linux-x64", "blender",
    ),
)


def find_blender():
    """Return a Blender executable path, or None if none is found."""
    for cand in (BLENDER, "blender"):
        if os.path.sep in cand and os.path.exists(cand):
            return cand
        if os.path.sep not in cand:
            for d in os.environ.get("PATH", "").split(os.pathsep):
                if os.path.exists(os.path.join(d, cand)):
                    return cand
    return None


def _run_blender(args, timeout=300):
    exe = find_blender()
    if exe is None:
        return None, "Blender was not found. Set BLENQ_BLENDER to the Blender executable."
    cmd = [exe, "--background", "--python", JOB, "--"] + args
    try:
        proc = subprocess.run(
            cmd, capture_output=True, text=True, timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return None, "Blender timed out."
    return proc, None


def run_scripts(jobs, timeout=600):
    """Run a list of scripts inside one Blender process.

    jobs: list of {"id": str, "object": str, "script": str,
                   "expected": int}
    Returns (results, error): results is a list of
    {"id": str, "ok": bool, "count": int, "error": str or None}.
    """
    with tempfile.TemporaryDirectory() as td:
        inp = os.path.join(td, "in.json")
        outp = os.path.join(td, "out.json")
        with open(inp, "w") as f:
            json.dump(jobs, f)
        proc, err = _run_blender(
            ["--mode", "validate", "--input", inp, "--output", outp],
            timeout=timeout,
        )
        if err:
            return None, err
        if proc.returncode != 0:
            return None, (
                "Blender exited with code "
                f"{proc.returncode}: {(proc.stderr or proc.stdout)[-500:]}"
            )
        with open(outp) as f:
            return json.load(f), None


def render_script(script, out_png, timeout=300):
    """Build the model from `script` in Blender and render a picture.

    Returns (ok, error): ok is True when the picture was written.
    """
    with tempfile.TemporaryDirectory() as td:
        inp = os.path.join(td, "script.py")
        with open(inp, "w") as f:
            f.write(script)
        proc, err = _run_blender(
            ["--mode", "render", "--input", inp, "--output", out_png],
            timeout=timeout,
        )
        if err:
            return False, err
        if proc.returncode != 0:
            return False, (
                "Blender exited with code "
                f"{proc.returncode}: {(proc.stderr or proc.stdout)[-500:]}"
            )
        if not os.path.exists(out_png) or os.path.getsize(out_png) == 0:
            return False, "Blender did not write a picture."
        return True, None


if __name__ == "__main__":
    print("Blender:", find_blender())
    sys.exit(0 if find_blender() else 1)
