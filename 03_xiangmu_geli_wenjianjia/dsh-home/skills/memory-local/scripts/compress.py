"""
Memory-Local 压缩/摘要模块
独立的压缩逻辑，可由 cron 定时触发或手动调用
"""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Any
from .memory_core import get_memory_store


def compress_old_memories(days: int = None, keep_raw_days: int = None, 
                          summary_model: str = None, summary_max_chars: int = 500) -> Dict[str, Any]:
    """
    压缩旧记忆为摘要
    
    Args:
        days: 压缩多少天前的记忆（默认用配置文件）
        keep_raw_days: 保留原文天数（默认用配置文件）
        summary_model: 摘要模型（默认用配置文件）
        summary_max_chars: 摘要最大字符数
        
    Returns:
        压缩统计结果
    """
    store = get_memory_store()
    
    # 使用配置文件默认值
    config = store.config['compression']
    days = days or 30
    keep_raw_days = keep_raw_days or config['keep_raw_days']
    summary_model = summary_model or config['summary_model']
    summary_max_chars = summary_max_chars or config['summary_max_chars']
    
    cutoff_date = datetime.now() - timedelta(days=keep_raw_days)
    cutoff_str = cutoff_date.isoformat()
    
    # 查询所有记忆
    all_mem = store.collection.get(include=['documents', 'metadatas'])
    
    # 按会话分组需要压缩的记忆
    sessions_to_compress = {}
    for i, meta in enumerate(all_mem.get('metadatas', [])):
        created = meta.get('created_at', '')
        mem_type = meta.get('type', 'fact')
        
        # 只压缩 fact 类型且超过保留期的
        if created < cutoff_str and mem_type == 'fact':
            sid = meta.get('session_id', 'unknown')
            if sid not in sessions_to_compress:
                sessions_to_compress[sid] = []
            sessions_to_compress[sid].append({
                'id': all_mem['ids'][i],
                'content': all_mem['documents'][i],
                'metadata': meta
            })
    
    results = {
        'sessions_processed': 0,
        'memories_compressed': 0,
        'summaries_created': 0,
        'errors': []
    }
    
    # 对每个旧会话生成摘要
    for sid, mems in sessions_to_compress.items():
        if len(mems) < 3:
            continue
        
        try:
            # 构建压缩提示
            content = "\n".join([f"- {m['content']}" for m in mems])
            prompt = f"""请将以下对话记忆压缩为一段不超过{summary_max_chars}字的摘要，保留关键事实、偏好、决定：

{content}

摘要："""
            
            # 调用本地小模型生成摘要
            resp = store.ollama_client.chat(
                model=summary_model,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.3, 'num_predict': summary_max_chars}
            )
            summary = resp['message']['content'].strip()
            
            # 删除原始记忆
            ids_to_delete = [m['id'] for m in mems]
            store.collection.delete(ids=ids_to_delete)
            
            # 写入摘要
            store.add(
                content=f"[会话摘要] {summary}",
                metadata={
                    'type': 'summary',
                    'source': 'compression',
                    'session_id': sid,
                    'original_count': len(mems),
                    'compressed_at': datetime.now().isoformat()
                }
            )
            
            results['sessions_processed'] += 1
            results['memories_compressed'] += len(mems)
            results['summaries_created'] += 1
            
        except Exception as e:
            results['errors'].append(f"Session {sid}: {str(e)}")
    
    return results


def compress_session(session_id: str, summary_model: str = None, 
                     summary_max_chars: int = 500) -> Dict[str, Any]:
    """
    压缩指定会话的所有记忆
    """
    store = get_memory_store()
    config = store.config['compression']
    summary_model = summary_model or config['summary_model']
    summary_max_chars = summary_max_chars or config['summary_max_chars']
    
    # 查询该会话的所有 fact 记忆
    all_mem = store.collection.get(
        where={"$and": [{"session_id": {"$eq": session_id}}, {"type": {"$eq": "fact"}}]},
        include=['documents', 'metadatas']
    )
    
    mems = []
    for i, mem_id in enumerate(all_mem.get('ids', [])):
        mems.append({
            'id': mem_id,
            'content': all_mem['documents'][i],
            'metadata': all_mem['metadatas'][i]
        })
    
    if len(mems) < 3:
        return {'error': f'Session {session_id} has less than 3 memories, skipping compression'}
    
    # 压缩
    content = "\n".join([f"- {m['content']}" for m in mems])
    prompt = f"""请将以下对话记忆压缩为一段不超过{summary_max_chars}字的摘要，保留关键事实、偏好、决定：

{content}

摘要："""
    
    try:
        resp = store.ollama_client.chat(
            model=summary_model,
            messages=[{'role': 'user', 'content': prompt}],
            options={'temperature': 0.3, 'num_predict': summary_max_chars}
        )
        summary = resp['message']['content'].strip()
        
        # 删除原始记忆
        ids_to_delete = [m['id'] for m in mems]
        store.collection.delete(ids=ids_to_delete)
        
        # 写入摘要
        store.add(
            content=f"[会话摘要] {summary}",
            metadata={
                'type': 'summary',
                'source': 'compression',
                'session_id': session_id,
                'original_count': len(mems),
                'compressed_at': datetime.now().isoformat()
            }
        )
        
        return {
            'success': True,
            'session_id': session_id,
            'memories_compressed': len(mems),
            'summary': summary
        }
    except Exception as e:
        return {'error': str(e)}


def get_compression_stats() -> Dict[str, Any]:
    """获取压缩相关统计"""
    store = get_memory_store()
    all_mem = store.collection.get(include=['metadatas'])
    
    fact_count = 0
    summary_count = 0
    old_facts = 0
    cutoff = datetime.now() - timedelta(days=store.config['compression']['keep_raw_days'])
    cutoff_str = cutoff.isoformat()
    
    for meta in all_mem.get('metadatas', []):
        if meta.get('type') == 'fact':
            fact_count += 1
            if meta.get('created_at', '') < cutoff_str:
                old_facts += 1
        elif meta.get('type') == 'summary':
            summary_count += 1
    
    return {
        'total_facts': fact_count,
        'old_facts_need_compress': old_facts,
        'summaries': summary_count,
        'keep_raw_days': store.config['compression']['keep_raw_days']
    }


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "stats":
        print(json.dumps(get_compression_stats(), indent=2, ensure_ascii=False))
    elif len(sys.argv) > 1 and sys.argv[1] == "session":
        if len(sys.argv) < 3:
            print("Usage: python compress.py session <session_id>")
        else:
            print(json.dumps(compress_session(sys.argv[2]), indent=2, ensure_ascii=False))
    else:
        print(json.dumps(compress_old_memories(), indent=2, ensure_ascii=False))