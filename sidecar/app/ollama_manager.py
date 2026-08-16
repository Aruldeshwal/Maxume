"""Dynamic Local Ollama Tags Discovery & VRAM Guardrail Manager."""

import os
import requests
from typing import List, Dict, Any, Optional

DEFAULT_OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434")
DEFAULT_VRAM_BUDGET_GB = float(os.environ.get("MAXUME_VRAM_BUDGET_GB", "5.2"))
DEFAULT_CONTEXT_LIMIT = int(os.environ.get("OLLAMA_CONTEXT_LIMIT", "2048"))

# VRAM Constants (Reconciled from difficulties.md §1 & architecture.md §3)
RUNTIME_OVERHEAD_GB = 0.4  # Base framework & OS buffer overhead
KV_CACHE_MB_PER_TOKEN = 0.15 / 1024.0  # ~0.15MB per token in FP16 for 7B Q4_K_M (in GB)

def calculate_vram_requirement(model_size_bytes: int, num_ctx: int = 2048) -> float:
    """
    Calculate estimated VRAM requirement in GB:
    Model file size in GB + Runtime overhead (~0.4GB) + KV cache footprint (num_ctx * ~0.15MB)
    """
    model_size_gb = model_size_bytes / (1024.0 ** 3)
    kv_cache_gb = num_ctx * (0.15 / 1024.0)
    total_vram_gb = model_size_gb + RUNTIME_OVERHEAD_GB + kv_cache_gb
    return round(total_vram_gb, 2)

def evaluate_model_vram_guardrail(
    model_name: str,
    model_size_bytes: int,
    num_ctx: int = 2048,
    budget_gb: float = DEFAULT_VRAM_BUDGET_GB
) -> Dict[str, Any]:
    """
    Evaluates whether candidate Ollama model fits within local VRAM budget.
    """
    req_vram = calculate_vram_requirement(model_size_bytes, num_ctx)
    fits = req_vram <= budget_gb

    warning_msg = None
    if not fits:
        warning_msg = (
            f"Target model '{model_name}' requires ~{req_vram}GB VRAM, exceeding local budget ({budget_gb}GB). "
            "Loading it will force CPU layer offloading, dropping throughput from ~60 tok/s to ~5–8 tok/s. "
            "Switch to Qwen 2.5 7B Q4_K_M, or reduce context to 1024 tokens."
        )

    return {
        "model_name": model_name,
        "model_size_gb": round(model_size_bytes / (1024.0 ** 3), 2),
        "num_ctx": num_ctx,
        "estimated_vram_gb": req_vram,
        "vram_budget_gb": budget_gb,
        "fits_vram": fits,
        "warning": warning_msg
    }

class OllamaManager:
    def __init__(self, base_url: str = DEFAULT_OLLAMA_BASE_URL):
        self.base_url = base_url.rstrip("/")

    def get_status(self) -> Dict[str, Any]:
        """Check if local Ollama daemon is reachable."""
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=2.0)
            if res.status_code == 200:
                return {"online": True, "base_url": self.base_url}
            return {"online": False, "error": f"HTTP {res.status_code}", "base_url": self.base_url}
        except Exception as e:
            return {"online": False, "error": str(e), "base_url": self.base_url}

    def list_models(self, num_ctx: int = DEFAULT_CONTEXT_LIMIT, budget_gb: float = DEFAULT_VRAM_BUDGET_GB) -> Dict[str, Any]:
        """
        Queries GET /api/tags from Ollama and evaluates VRAM guardrails for each model.
        """
        try:
            res = requests.get(f"{self.base_url}/api/tags", timeout=2.5)
            if res.status_code != 200:
                return {
                    "online": False,
                    "models": [],
                    "error": f"Ollama returned status {res.status_code}"
                }
            
            data = res.json()
            raw_models = data.get("models", [])
            evaluated_models = []

            for m in raw_models:
                name = m.get("name", "")
                size_bytes = m.get("size", 0)
                details = m.get("details", {})
                
                guardrail = evaluate_model_vram_guardrail(
                    model_name=name,
                    model_size_bytes=size_bytes,
                    num_ctx=num_ctx,
                    budget_gb=budget_gb
                )

                evaluated_models.append({
                    "name": name,
                    "model": m.get("model", name),
                    "size_bytes": size_bytes,
                    "parameter_size": details.get("parameter_size", "unknown"),
                    "quantization_level": details.get("quantization_level", "unknown"),
                    "modified_at": m.get("modified_at"),
                    **guardrail
                })

            return {
                "online": True,
                "models": evaluated_models,
                "count": len(evaluated_models),
                "active_context_limit": num_ctx,
                "vram_budget_gb": budget_gb
            }
        except Exception as e:
            return {
                "online": False,
                "models": [],
                "error": str(e),
                "notice": "Offline Mode Active. Cloud integrations (Gemini, Groq, CSE) are suspended. Local projects watcher is active."
            }

ollama_manager = OllamaManager()
