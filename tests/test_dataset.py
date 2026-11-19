"""BlenQ tests — dataset."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import tokenize  # noqa: E402
from objects import OBJECTS  # noqa: E402
from validate import validate  # noqa: E402

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(HERE, "data")


def _load(name):
    with open(os.path.join(DATA, name)) as f:
        return [json.loads(line) for line in f if line.strip()]


def test_dataset_total():
    rows = _load("dataset.jsonl")
    assert len(rows) == 16000


def test_splits():
    assert len(_load("train.jsonl")) == 12800
    assert len(_load("val.jsonl")) == 1600
    assert len(_load("test.jsonl")) == 1600


def test_splits_do_not_overlap():
    train = {r["input"] for r in _load("train.jsonl")}
    val = {r["input"] for r in _load("val.jsonl")}
    test = {r["input"] for r in _load("test.jsonl")}
    assert not (train & val) and not (train & test) and not (val & test)


def test_no_duplicate_prompts():
    rows = _load("dataset.jsonl")
    prompts = [r["input"] for r in rows]
    assert len(set(prompts)) == len(prompts)


def test_per_object_counts():
    rows = _load("dataset.jsonl")
    from collections import Counter
    counts = Counter(r["object"] for r in rows)
    assert set(counts) == set(OBJECTS)
    for name, n in counts.items():
        assert 1000 <= n <= 1100, (name, n)


def test_rows_have_required_fields():
    for r in _load("dataset.jsonl")[:500]:
        assert r["object"] in OBJECTS
        assert r["size"] in ("small", "medium", "large")
        assert r["colour"] in OBJECTS[r["object"]]["colours"]
        assert r["input"] and r["script"].startswith("import bpy")


def test_every_script_validates():
    bad = []
    for r in _load("dataset.jsonl"):
        ok, obj, err = validate(r["script"])
        if not ok or obj != r["object"]:
            bad.append((r["object"], obj, err))
    assert bad == []


def test_scripts_fit_context():
    lens = [len(tokenize(r["script"])) for r in _load("dataset.jsonl")]
    assert max(lens) <= 512
    assert min(lens) >= 200


def test_vocab_covers_dataset():
    with open(os.path.join(DATA, "vocab.json")) as f:
        vocab = json.load(f)
    assert len(vocab) >= 100
    for tok in ("<pad>", "<unk>", "<bos>", "<eos>"):
        assert tok in vocab
    for r in _load("dataset.jsonl")[:1000]:
        for t in tokenize(r["input"].lower()) + tokenize(r["script"]):
            assert t in vocab, t


def test_prompts_are_varied():
    rows = _load("dataset.jsonl")
    first_words = {r["input"].split()[0] for r in rows}
    assert len(first_words) >= 8  # not one repeated template
