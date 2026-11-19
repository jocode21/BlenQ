"""BlenQ tests — script validator."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from objects import OBJECTS, build_script  # noqa: E402
from validate import validate  # noqa: E402


def test_all_default_scripts_validate():
    for name in OBJECTS:
        ok, obj, err = validate(build_script(name))
        assert ok and obj == name, (name, err)


def test_all_135_scripts_validate():
    for name in OBJECTS:
        for size in ("small", "medium", "large"):
            for colour in OBJECTS[name]["colours"]:
                ok, obj, err = validate(build_script(name, size, colour))
                assert ok and obj == name, (name, size, colour, err)


def test_empty_rejected():
    ok, _, err = validate("")
    assert not ok and err


def test_os_access_rejected():
    ok, _, _ = validate("import bpy\nimport os\nos.system('x')")
    assert not ok


def test_eval_rejected():
    ok, _, _ = validate("import bpy\neval('1+1')")
    assert not ok


def test_wm_ops_rejected():
    ok, _, _ = validate(
        "import bpy\nbpy.ops.wm.save_as_mainfile(filepath='/tmp/x.blend')")
    assert not ok


def test_missing_import_rejected():
    ok, _, _ = validate(build_script("sword").replace("import bpy", "import sys"))
    assert not ok


def test_wrong_piece_count_rejected():
    # Axe has 5 pieces; dropping one leaves 4, below the 5 minimum.
    script = build_script("axe")
    lines = script.splitlines()
    dropped = [ln for ln in lines
               if not ln.startswith("bpy.ops.mesh.primitive_cone_add")]
    assert len(dropped) < len(lines)
    ok, _, err = validate("\n".join(dropped))
    assert not ok


def test_missing_colour_loop_rejected():
    script = build_script("sword")
    kept = [ln for ln in script.splitlines()
            if not ln.startswith("for o in bpy.context.scene.objects:")]
    ok, _, _ = validate("\n".join(kept))
    assert not ok


def test_sql_injection_style_prompt_rejected():
    ok, _, _ = validate("DROP TABLE students;")
    assert not ok


def test_wellformed_unknown_script_accepted():
    # A well-formed BlenQ-style script that is not one of the 135
    # known ones is accepted (object None) — Blender decides.
    # Sword's blade really is scale=(0.12, 0.04, 0.9); nudge it.
    script = build_script("sword").replace(
        "scale=(0.12, 0.04, 0.9)", "scale=(0.13, 0.04, 0.9)")
    ok, obj, err = validate(script)
    assert ok and obj is None and err is None
