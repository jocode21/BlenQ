"""BlenQ tests — object definitions and script building."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import detokenize, tokenize  # noqa: E402
from objects import OBJECTS, SIZES, build_script, piece_count  # noqa: E402

EXPECTED_OBJECTS = {
    "sword", "shield", "axe", "war hammer", "dagger", "helmet",
    "crown", "rocket", "car", "boat", "castle tower", "house",
    "tree", "robot", "treasure chest",
}


def test_fifteen_objects():
    assert set(OBJECTS) == EXPECTED_OBJECTS
    assert len(OBJECTS) == 15


def test_piece_counts_in_range():
    for name in OBJECTS:
        n = piece_count(name)
        assert 5 <= n <= 8, (name, n)


def test_sizes():
    assert SIZES == {"small": 0.8, "medium": 1.0, "large": 1.2}


def test_sizes_change_script():
    small = build_script("sword", "small")
    large = build_script("sword", "large")
    assert small != large
    assert "0.96" in large or "1.2" in large


def test_colours_change_script():
    a = build_script("car", "medium", "red")
    b = build_script("car", "medium", "blue")
    assert a != b


def test_default_colour_is_first():
    for name in OBJECTS:
        first = next(iter(OBJECTS[name]["colours"]))
        assert build_script(name) == build_script(name, "medium", first)


def test_each_object_has_three_colours():
    for name in OBJECTS:
        assert len(OBJECTS[name]["colours"]) == 3, name


def test_scripts_are_readable():
    for name in OBJECTS:
        script = build_script(name)
        assert script.startswith("import bpy\n")
        assert "bpy.ops.mesh.primitive_" in script
        assert "for o in bpy.context.scene.objects:" in script


def test_tokenizer_roundtrip_all_objects():
    for name in OBJECTS:
        script = build_script(name)
        assert detokenize(tokenize(script)) == script, name


def test_script_token_lengths():
    for name in OBJECTS:
        n = len(tokenize(build_script(name)))
        assert n <= 512, (name, n)


@pytest.mark.parametrize("name", sorted(OBJECTS))
def test_object_script_has_expected_piece_count(name):
    script = build_script(name)
    lines = [ln for ln in script.splitlines()
             if ln.startswith("bpy.ops.mesh.primitive_")]
    assert len(lines) == piece_count(name)
