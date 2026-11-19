"""BlenQ tests — model shape, tokenizer, training guardrails."""
import os
import sys

import torch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from model import (  # noqa: E402
    CONFIG, build_model, count_parameters, detokenize, tokenize,
)


def test_config():
    assert CONFIG["d_model"] == 256
    assert CONFIG["num_encoder_layers"] == 3
    assert CONFIG["num_decoder_layers"] == 3
    assert CONFIG["max_len"] == 512


def test_parameter_count_in_range():
    model, _ = build_model(187)
    n = count_parameters(model)
    assert 10_000_000 <= n <= 20_000_000, n


def test_forward_pass_shape():
    vocab_size = 187
    model, _ = build_model(vocab_size)
    model.eval()
    src = torch.randint(4, vocab_size, (2, 6))
    tgt = torch.randint(4, vocab_size, (2, 10))
    with torch.no_grad():
        out = model(src, tgt)
    assert out.shape == (2, 10, vocab_size)


def test_tokenizer_keeps_newlines():
    toks = tokenize("import bpy\nbpy.ops.mesh.primitive_cube_add()")
    assert "\n" in toks
    assert detokenize(toks) == "import bpy\nbpy.ops.mesh.primitive_cube_add()"


def test_tokenizer_numbers_and_dots():
    script = "scale=(0.08, 0.5, 0.08)"
    assert detokenize(tokenize(script)) == script


def test_requirements_use_cuda_torch():
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(here, "requirements.txt")) as f:
        text = f.read()
    assert "cu132" in text
    assert "torch==2.15.0+cpu" not in text


def test_full_training_refuses_cpu():
    from types import SimpleNamespace

    import train

    args = SimpleNamespace(full=True, device="cpu", smoke=False,
                           epochs=30, limit=0, batch_size=16, lr=3e-4,
                           seed=42, eval_limit=200)
    try:
        train.train(args)
    except SystemExit as e:
        assert "CPU" in str(e) or "cuda" in str(e).lower()
    else:
        raise AssertionError("--full on CPU must refuse to train")
