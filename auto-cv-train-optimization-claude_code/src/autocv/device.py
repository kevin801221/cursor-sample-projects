"""自動挑選運算裝置：auto → mps → cuda → cpu。"""

from __future__ import annotations

import os


def _mps_available() -> bool:
    try:
        import torch

        return torch.backends.mps.is_available()
    except Exception:
        return False


def _cuda_available() -> bool:
    try:
        import torch

        return torch.cuda.is_available()
    except Exception:
        return False


def pick_device(pref: str = "auto") -> str:
    """pref 非 auto 時原樣回傳；auto 時 mps→cuda→cpu 依序挑。"""
    if pref != "auto":
        return pref
    if _mps_available():
        os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
        return "mps"
    if _cuda_available():
        return "cuda"
    return "cpu"
