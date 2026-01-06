"""Top-level fusion package wrapper.

Exposes `fuse()` so other modules (like `backend/app.py`) can do
`from fusion import fuse` without depending on backend internals.
"""
from typing import Any, Dict

# Import the implementation from backend.fus to keep a single source
# of truth for fusion logic.
try:
    from backend.fus import fuse as _impl_fuse  # type: ignore
except Exception:  # pragma: no cover - allow tests to import even if backend missing
    _impl_fuse = None


def fuse(vision: Dict[str, Any], voice: Dict[str, Any], **kwargs) -> Dict[str, Any]:
    if _impl_fuse is None:
        raise RuntimeError("Fusion implementation not available")
    return _impl_fuse(vision, voice, **kwargs)


__all__ = ["fuse"]
