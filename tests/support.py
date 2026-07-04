from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType


def load_hook_module() -> ModuleType:
    hook_path = Path(__file__).resolve().parents[1] / ".claude" / "hooks" / "block_destructive_bash.py"
    spec = importlib.util.spec_from_file_location("block_destructive_bash", hook_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load hook module from {hook_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
