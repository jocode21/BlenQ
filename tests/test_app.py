"""BlenQ tests — web app endpoints (no trained model needed)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import app as app_module  # noqa: E402


@pytest.fixture()
def client():
    app_module.app.config["TESTING"] = True
    with app_module.app.test_client() as c:
        yield c


def test_index_200_and_title(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"BlenQ" in r.data


def test_index_has_no_example_prompts(client):
    r = client.get("/")
    text = r.data.decode()
    # No suggested/example prompts anywhere in the UI.
    assert "example" not in text.lower()
    assert "try:" not in text.lower()
    assert "Try saying" not in text


def test_index_has_no_forbidden_words(client):
    r = client.get("/")
    text = r.data.decode()
    assert "part" not in text.lower()
    assert "VM" not in text
    assert "virtual machine" not in text.lower()


def test_metrics_page_200(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert b"Metrics" in r.data or b"metrics" in r.data


def test_objects_endpoint_lists_15(client):
    r = client.get("/objects")
    assert r.status_code == 200
    data = r.get_json()
    assert len(data) == 15
    names = {o["name"] for o in data}
    assert "sword" in names and "treasure chest" in names
    for o in data:
        assert 5 <= o["pieces"] <= 8


def test_generate_empty_prompt(client):
    r = client.post("/generate", json={"prompt": ""})
    assert r.status_code == 200
    assert r.get_json()["ok"] is False


def test_generate_without_model_fails_cleanly(client, monkeypatch):
    # Simulate "no trained model yet": the endpoint must say so,
    # not crash with a 500. (Patched so this holds whether or not a
    # model file happens to exist on disk right now.)
    def _missing(*args, **kwargs):
        raise FileNotFoundError("No trained model at data/model.pt.")

    monkeypatch.setattr(app_module, "get_model", _missing)
    r = client.post("/generate", json={"prompt": "make a sword"})
    assert r.status_code == 200
    data = r.get_json()
    assert data["ok"] is False
    assert "model" in data["error"].lower() or "train" in data["error"].lower()


def test_render_empty_script(client):
    r = client.post("/render", json={"script": ""})
    assert r.status_code == 200
    assert r.get_json()["ok"] is False


def test_render_bad_script_rejected(client):
    r = client.post("/render", json={"script": "import os\nos.system('x')"})
    assert r.status_code == 200
    assert r.get_json()["ok"] is False
