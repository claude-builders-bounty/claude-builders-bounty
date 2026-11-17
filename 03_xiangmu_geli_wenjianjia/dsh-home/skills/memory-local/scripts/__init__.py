"""
Memory-Local: Local Vector Memory with Ollama bge-m3 + ChromaDB
"""

from .memory_core import MemoryStore, get_memory_store
from .hooks import (
    on_session_start,
    on_turn_end,
    on_session_end,
    main as cli_main
)
from .compress import (
    compress_old_memories,
    compress_session,
    get_compression_stats
)

__version__ = "1.0.0"
__all__ = [
    "MemoryStore",
    "get_memory_store",
    "on_session_start",
    "on_turn_end",
    "on_session_end",
    "cli_main",
    "compress_old_memories",
    "compress_session",
    "get_compression_stats"
]