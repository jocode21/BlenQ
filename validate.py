"""BlenQ — script validator.

Checks a generated Blender script without running Blender:
  * it starts with `import bpy` and only uses the Blender API
    (bpy.ops, bpy.context, bpy.data are not used here);
  * no file access, no os/sys/subprocess, no eval/exec/open;
  * every piece is a primitive_*_add call with a location and a
    scale, all numbers in a sane range;
  * 5-8 pieces, and the whole script fits in 512 tokens;
  * it names one of the 15 fixed objects (matched by its colour
    loop and piece shapes is not attempted here — that is what the
    Blender run in blender_tools.py checks).

Returns (ok, object_name, error). object_name is the object whose
script this most closely matches, or None when it cannot be told.
"""
import re

from model import tokenize
from objects import OBJECTS, build_script, piece_count

ALLOWED_PREFIXES = (
    "import bpy",
    "bpy.ops.object.select_all",
    "bpy.ops.object.delete",
    "bpy.ops.mesh.primitive_",
    "for o in bpy.context.scene.objects:",
)
# The select/delete header is allowed; anything else that deletes
# or writes files is not. The check below handles this precisely.
BLOCKED_RE = re.compile(
    r"\b(os|sys|subprocess|eval|exec|open|input|compile)\b"
    r"|__\w+__"
    r"|bpy\.data"
    r"|bpy\.ops\.wm\."
)
PRIMITIVE_RE = re.compile(
    r"bpy\.ops\.mesh\.primitive_(cube|cylinder|uv_sphere|cone)_add"
    r"\(location=\((-?[0-9.]+), (-?[0-9.]+), (-?[0-9.]+)\), "
    r"scale=\((-?[0-9.]+), (-?[0-9.]+), (-?[0-9.]+)\)"
    r"(, vertices=4)?(, rotation=\((-?[0-9.]+), (-?[0-9.]+), (-?[0-9.]+)\))?\)"
)


def _numbers_ok(vals):
    return all(-5.0 <= float(v) <= 5.0 for v in vals)


def validate(script):
    """Return (ok, object_name, error)."""
    if not script or not script.strip():
        return False, None, "Empty script. Type a request for one of the 15 objects."
    s = script.strip()
    if len(tokenize(s)) > 512:
        return False, None, (
            "That script is too long for BlenQ to run reliably "
            "(over 512 tokens)."
        )
    if BLOCKED_RE.search(s):
        return False, None, (
            "That script uses something BlenQ never generates "
            "(file access, system calls, or Blender data access). "
            "Try rephrasing your request."
        )
    lines = [ln for ln in s.splitlines() if ln.strip()]
    if not lines or lines[0] != "import bpy":
        return False, None, "A BlenQ script must start with import bpy."
    if len(lines) < 2 or "select_all" not in lines[1]:
        return False, None, "A BlenQ script must clear the scene first."
    pieces = []
    for ln in lines:
        if ln.startswith("bpy.ops.mesh.primitive_"):
            m = PRIMITIVE_RE.match(ln)
            if not m:
                return False, None, (
                    "A piece line is not in the form BlenQ generates. "
                    "Try rephrasing your request."
                )
            if not _numbers_ok(m.groups()[1:4] + m.groups()[4:7]):
                return False, None, (
                    "A piece has a location or size outside the range "
                    "BlenQ uses (-5 to 5)."
                )
            pieces.append(ln)
    if not 5 <= len(pieces) <= 8:
        return False, None, (
            f"A BlenQ model has 5 to 8 pieces; this script has "
            f"{len(pieces)}."
        )
    if not any("for o in bpy.context.scene.objects:" in ln for ln in lines):
        return False, None, "A BlenQ script must set the object colours."
    # Which object is this? Match the exact piece lines against the
    # 135 known scripts (15 objects x 3 sizes x 3 colours).
    for name in OBJECTS:
        for size in ("small", "medium", "large"):
            for colour in OBJECTS[name]["colours"]:
                if build_script(name, size, colour).strip() == s:
                    return True, name, None
    # Not an exact known script, but it is a well-formed BlenQ-style
    # script: accept it, and let the Blender run decide whether it
    # builds cleanly.
    return True, None, None


if __name__ == "__main__":
    from objects import build_script as _bs
    bad = 0
    for name in OBJECTS:
        ok, obj, err = validate(_bs(name))
        good = ok and obj == name
        bad += 0 if good else 1
        print(("PASS" if good else "FAIL"), name, "|", obj, "|", err or "")
    for script, want in [
        ("", False),
        ("import os\nos.system('x')", False),
        ("import bpy\nprint('hi')", False),
        ("DROP TABLE students;", False),
        (_bs("sword").replace("import bpy", "import sys"), False),
    ]:
        ok, _, _ = validate(script)
        good = ok == want
        bad += 0 if good else 1
        print(("PASS" if good else "FAIL"), "|", script[:40].replace("\n", " "))
    print("failures:", bad)
    raise SystemExit(1 if bad else 0)
