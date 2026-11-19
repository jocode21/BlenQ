"""BlenQ tests — Blender runs (headless). Slow: one batch job for
all 15 default scripts, then one assertion per object, plus one
real render whose PNG is checked on disk and read back."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from blender_tools import render_script, run_scripts  # noqa: E402
from objects import OBJECTS, build_script, piece_count  # noqa: E402


@pytest.fixture(scope="module")
def batch_results():
    jobs = [
        {"id": name, "object": name, "script": build_script(name),
         "expected": piece_count(name)}
        for name in OBJECTS
    ]
    results, err = run_scripts(jobs, timeout=900)
    assert err is None, err
    assert results is not None and len(results) == 15
    return {r["id"]: r for r in results}


@pytest.mark.parametrize("name", sorted(OBJECTS))
def test_object_builds_in_blender(name, batch_results):
    r = batch_results[name]
    assert r["error"] is None, (name, r["error"])
    assert r["ok"] is True, (name, r)
    assert r["count"] == piece_count(name), (name, r["count"])


def test_render_writes_png(tmp_path):
    out = str(tmp_path / "sword.png")
    ok, err = render_script(build_script("sword"), out)
    assert ok, err
    assert os.path.exists(out) and os.path.getsize(out) > 10_000
    with open(out, "rb") as f:
        assert f.read(8) == b"\x89PNG\r\n\x1a\n"
