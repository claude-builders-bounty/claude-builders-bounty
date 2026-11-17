"""
Memory-Local Hermes Hooks
自动集成到 Hermes 生命周期：session_start, turn_end, session_end
"""

from .memory_core import get_memory_store


# 全局存储实例
_store = None

def _get_store():
    global _store
    if _store is None:
        _store = get_memory_store()
    return _store


# ========== Hermes Hook 入口 ==========

def on_session_start(session_id: str, user_input: str = "") -> str:
    """
    Hermes session_start hook
    返回要注入到 system prompt 的记忆块
    """
    store = _get_store()
    store.start_session(session_id)
    
    if user_input:
        return store.inject_relevant_memories(user_input)
    return ""


def on_turn_end(session_id: str, user_msg: str, assistant_msg: str) -> None:
    """
    Hermes turn_end hook
    每轮对话结束时提取事实并缓存
    """
    store = _get_store()
    if store.current_session_id != session_id:
        store.start_session(session_id)
    store.on_turn_end(user_msg, assistant_msg)


def on_session_end(session_id: str) -> None:
    """
    Hermes session_end hook
    会话结束时刷新所有待写入记忆
    """
    store = _get_store()
    if store.current_session_id == session_id:
        store.end_session()


# ========== 手动调用命令 (供 CLI/skill run 使用) ==========

def cmd_search(query: str, top_k: int = 5, min_score: float = 0.35) -> str:
    """手动搜索记忆"""
    store = _get_store()
    results = store.search(query, top_k=top_k, min_score=min_score)
    if not results:
        return "No relevant memories found."
    
    lines = [f"Found {len(results)} memories for: {query}\n"]
    for i, mem in enumerate(results, 1):
        lines.append(f"{i}. [{mem['metadata'].get('type', 'fact')}] {mem['content']}")
        lines.append(f"   Score: {mem['score']} | Session: {mem['metadata'].get('session_id', '?')} | Turn: {mem['metadata'].get('turn', '?')}")
        lines.append("")
    return "\n".join(lines)


def cmd_stats() -> str:
    """查看统计"""
    store = _get_store()
    stats = store.stats()
    lines = [
        f"Total memories: {stats['total_memories']}",
        f"Embed model: {stats['embed_model']}",
        f"Persist dir: {stats['persist_dir']}",
        "",
        "By type:"
    ]
    for t, c in stats['by_type'].items():
        lines.append(f"  {t}: {c}")
    return "\n".join(lines)


def cmd_compress() -> str:
    """强制压缩"""
    store = _get_store()
    store._maybe_compress()
    return "Compression check completed."


def cmd_add(content: str, metadata: dict = None) -> str:
    """手动添加记忆"""
    store = _get_store()
    mem_id = store.add(content, metadata or {})
    return f"Added memory: {mem_id}"


def cmd_delete(memory_ids: list) -> str:
    """手动删除记忆"""
    store = _get_store()
    count = store.delete(memory_ids)
    return f"Deleted {count} memories."


# ========== 供 skill run 调用的主入口 ==========

def main(args: list) -> str:
    """
    CLI 入口：hermes skill run memory-local <command> [args]
    
    Commands:
      search "query" [top_k] [min_score]
      stats
      compress
      add "content" [json_metadata]
      delete id1 id2 ...
    """
    if not args:
        return "Usage: memory-local <search|stats|compress|add|delete> [args]"
    
    cmd = args[0]
    
    if cmd == "search":
        if len(args) < 2:
            return "Usage: memory-local search \"query\" [top_k] [min_score]"
        query = args[1]
        top_k = int(args[2]) if len(args) > 2 else 5
        min_score = float(args[3]) if len(args) > 3 else 0.35
        return cmd_search(query, top_k, min_score)
    
    elif cmd == "stats":
        return cmd_stats()
    
    elif cmd == "compress":
        return cmd_compress()
    
    elif cmd == "add":
        if len(args) < 2:
            return "Usage: memory-local add \"content\" [json_metadata]"
        content = args[1]
        metadata = {}
        if len(args) > 2:
            import json
            try:
                metadata = json.loads(args[2])
            except:
                return "Invalid JSON metadata"
        return cmd_add(content, metadata)
    
    elif cmd == "delete":
        if len(args) < 2:
            return "Usage: memory-local delete id1 id2 ..."
        return cmd_delete(args[1:])
    
    else:
        return f"Unknown command: {cmd}"


if __name__ == "__main__":
    import sys
    print(main(sys.argv[1:]))