"""Unit tests for Dynamic Ollama tags lookup and VRAM guardrail calculations."""

import pytest
from unittest.mock import patch, MagicMock
from app.ollama_manager import (
    OllamaManager,
    calculate_vram_requirement,
    evaluate_model_vram_guardrail,
)

def test_vram_calculation_reconciled():
    """Verify VRAM calculation matches figures in difficulties.md §1."""
    # 4.4GB model file (4.4 * 1024^3 bytes)
    model_size_bytes = int(4.4 * (1024 ** 3))
    
    # 2K context limit (Maxume default)
    vram_2k = calculate_vram_requirement(model_size_bytes, num_ctx=2048)
    assert 5.0 <= vram_2k <= 5.2

    # 16K context limit (swelling KV cache)
    vram_16k = calculate_vram_requirement(model_size_bytes, num_ctx=16384)
    assert 7.0 <= vram_16k <= 7.3

def test_vram_guardrail_evaluation():
    """Verify in-UI hardware warning triggers on models exceeding budget."""
    budget = 5.2

    # 7B Q4 fits budget at 2048 context
    size_7b = int(4.4 * (1024 ** 3))
    res_7b = evaluate_model_vram_guardrail("qwen2.5:7b-instruct", size_7b, num_ctx=2048, budget_gb=budget)
    assert res_7b["fits_vram"] is True
    assert res_7b["warning"] is None

    # 14B Q4 (~9.0GB) exceeds budget
    size_14b = int(9.0 * (1024 ** 3))
    res_14b = evaluate_model_vram_guardrail("qwen2.5:14b", size_14b, num_ctx=2048, budget_gb=budget)
    assert res_14b["fits_vram"] is False
    assert res_14b["warning"] is not None
    assert "exceeding local budget" in res_14b["warning"]
    assert "CPU layer offloading" in res_14b["warning"]

def test_ollama_manager_list_models_mock():
    """Verify dynamic discovery parsing and formatting."""
    manager = OllamaManager(base_url="http://mock-ollama:11434")

    mock_tags_response = {
        "models": [
            {
                "name": "qwen2.5:7b-instruct",
                "model": "qwen2.5:7b-instruct",
                "size": int(4.4 * (1024 ** 3)),
                "details": {
                    "parameter_size": "7B",
                    "quantization_level": "Q4_K_M"
                },
                "modified_at": "2026-08-14T00:00:00Z"
            },
            {
                "name": "qwen2.5:14b",
                "model": "qwen2.5:14b",
                "size": int(9.0 * (1024 ** 3)),
                "details": {
                    "parameter_size": "14B",
                    "quantization_level": "Q4_K_M"
                },
                "modified_at": "2026-08-14T00:00:00Z"
            }
        ]
    }

    with patch("requests.get") as mock_get:
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = mock_tags_response

        catalog = manager.list_models(num_ctx=2048, budget_gb=5.2)
        assert catalog["online"] is True
        assert catalog["count"] == 2
        
        m1 = catalog["models"][0]
        assert m1["name"] == "qwen2.5:7b-instruct"
        assert m1["fits_vram"] is True

        m2 = catalog["models"][1]
        assert m2["name"] == "qwen2.5:14b"
        assert m2["fits_vram"] is False
        assert m2["warning"] is not None

def test_ollama_manager_offline_graceful():
    """Verify graceful fallback notice when Ollama daemon is offline."""
    manager = OllamaManager(base_url="http://invalid-localhost:9999")
    with patch("requests.get", side_effect=Exception("Connection refused")):
        catalog = manager.list_models()
        assert catalog["online"] is False
        assert catalog["models"] == []
        assert "Offline Mode Active" in catalog["notice"]
