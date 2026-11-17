"""
Memory-Local 核心模块
Ollama(bge-m3) + ChromaDB 本地向量记忆系统
"""

import os
import json
import uuid
import time
import hashlib
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import chromadb
from chromadb.config import Settings
import ollama
import yaml


class MemoryStore:
    """本地向量记忆存储 - 单例模式"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        
        # 加载配置
        self.config = self._load_config()
        
        # 初始化 Ollama 客户端
        self.ollama_client = ollama.Client(
            host=self.config['ollama']['host'],
            timeout=self.config['ollama']['timeout']
        )
        self.embed_model = self.config['ollama']['embed_model']
        
        # 初始化 ChromaDB
        self.chroma_client = chromadb.PersistentClient(
            path=self.config['chroma']['persist_dir'],
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 获取或创建集合
        self.collection = self.chroma_client.get_or_create_collection(
            name=self.config['chroma']['collection'],
            metadata={"hnsw:space": self.config['chroma']['hnsw_space']}
        )
        
        # 检索配置
        self.top_k = self.config['retrieval']['top_k']
        self.min_score = self.config['retrieval']['min_score']
        self.max_context_chars = self.config['retrieval']['max_context_chars']
        
        # 压缩配置
        self.compression_enabled = self.config['compression']['enabled']
        self.trigger_turns = self.config['compression']['trigger_turns']
        self.summary_model = self.config['compression']['summary_model']
        self.keep_raw_days = self.config['compression']['keep_raw_days']
        self.summary_max_chars = self.config['compression']['summary_max_chars']
        
        # Hook 配置
        self.auto_inject = self.config['hooks']['auto_inject_on_start']
        self.auto_save = self.config['hooks']['auto_save_on_end']
        self.save_every_n = self.config['hooks']['save_every_n_turns']
        
        # 会话状态
        self.current_session_id = None
        self.turn_count = 0
        self.pending_memories = []
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置文件"""
        skill_dir = Path(__file__).parent.parent
        config_path = skill_dir / "references" / "config.yaml"
        
        default_config = {
            'ollama': {'host': 'http://localhost:11434', 'embed_model': 'bge-m3', 'timeout': 30},
            'chroma': {'persist_dir': 'D:/Ai/Ollama/Memory/chroma', 'collection': 'hermes_memory', 'hnsw_space': 'cosine'},
            'retrieval': {'top_k': 5, 'min_score': 0.35, 'max_context_chars': 3000},
            'compression': {'enabled': True, 'trigger_turns': 20, 'summary_model': 'qwen2.5:7b-instruct-q3_K_M', 'keep_raw_days': 7, 'summary_max_chars': 500},
            'hooks': {'auto_inject_on_start': True, 'auto_save_on_end': True, 'save_every_n_turns': 5}
        }
        
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                user_config = yaml.safe_load(f)
                if user_config:
                    # 深度合并
                    self._deep_merge(default_config, user_config)
        
        return default_config
    
    def _deep_merge(self, base: dict, override: dict) -> dict:
        """深度合并字典"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
        return base
    
    def _embed(self, text: str) -> List[float]:
        """生成文本嵌入向量"""
        resp = self.ollama_client.embeddings(model=self.embed_model, prompt=text)
        return resp['embedding']
    
    def _generate_id(self, content: str, metadata: Dict) -> str:
        """基于内容生成确定性ID（去重用）"""
        key = f"{content}|{json.dumps(metadata, sort_keys=True)}"
        return hashlib.sha256(key.encode()).hexdigest()[:16]
    
    def add(self, content: str, metadata: Optional[Dict[str, Any]] = None, 
            memory_id: Optional[str] = None) -> str:
        """
        添加记忆（自动嵌入+去重）
        
        Args:
            content: 记忆内容
            metadata: 元数据，建议包含 type, source, session_id 等
            memory_id: 可选指定ID，不指定则基于内容哈希生成
            
        Returns:
            记忆ID
        """
        if metadata is None:
            metadata = {}
        
        metadata.setdefault('type', 'fact')
        metadata.setdefault('source', 'chat')
        metadata.setdefault('created_at', datetime.now().isoformat())
        metadata.setdefault('session_id', self.current_session_id or 'unknown')
        
        if memory_id is None:
            memory_id = self._generate_id(content, metadata)
        
        # 检查是否已存在
        existing = self.collection.get(ids=[memory_id])
        if existing['ids']:
            # 更新现有
            self.collection.update(
                ids=[memory_id],
                documents=[content],
                metadatas=[metadata]
            )
            return memory_id
        
        # 生成嵌入
        embedding = self._embed(content)
        
        # 存储
        self.collection.add(
            ids=[memory_id],
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata]
        )
        
        return memory_id
    
    def search(self, query: str, top_k: Optional[int] = None, 
               min_score: Optional[float] = None,
               filter_metadata: Optional[Dict] = None) -> List[Dict[str, Any]]:
        """
        语义检索记忆
        
        Args:
            query: 查询文本
            top_k: 返回数量
            min_score: 最小相似度阈值 (0-1, cosine similarity)
            filter_metadata: 元数据过滤条件
            
        Returns:
            记忆列表，每项包含 id, content, metadata, score
        """
        top_k = top_k or self.top_k
        min_score = min_score or self.min_score
        
        query_embedding = self._embed(query)
        
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_metadata,
            include=['documents', 'metadatas', 'distances']
        )
        
        memories = []
        if results['ids'] and results['ids'][0]:
            for i, mem_id in enumerate(results['ids'][0]):
                # Chroma 返回的是距离，转为相似度 (cosine: 1 - distance)
                distance = results['distances'][0][i]
                score = 1.0 - distance
                
                if score >= min_score:
                    memories.append({
                        'id': mem_id,
                        'content': results['documents'][0][i],
                        'metadata': results['metadatas'][0][i],
                        'score': round(score, 4)
                    })
        
        return memories
    
    def get(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """获取单条记忆"""
        result = self.collection.get(ids=[memory_id], include=['documents', 'metadatas'])
        if result['ids']:
            return {
                'id': result['ids'][0],
                'content': result['documents'][0],
                'metadata': result['metadatas'][0]
            }
        return None
    
    def update(self, memory_id: str, new_content: Optional[str] = None,
               new_metadata: Optional[Dict] = None) -> bool:
        """更新记忆"""
        existing = self.get(memory_id)
        if not existing:
            return False
        
        content = new_content if new_content is not None else existing['content']
        metadata = {**existing['metadata'], **(new_metadata or {})}
        metadata['updated_at'] = datetime.now().isoformat()
        
        embedding = self._embed(content)
        
        self.collection.update(
            ids=[memory_id],
            documents=[content],
            embeddings=[embedding],
            metadatas=[metadata]
        )
        return True
    
    def delete(self, memory_ids: List[str]) -> int:
        """删除记忆"""
        self.collection.delete(ids=memory_ids)
        return len(memory_ids)
    
    def stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        count = self.collection.count()
        # 简单统计类型分布
        all_mem = self.collection.get(include=['metadatas'])
        type_counts = {}
        for meta in all_mem.get('metadatas', []):
            t = meta.get('type', 'unknown')
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            'total_memories': count,
            'by_type': type_counts,
            'persist_dir': self.config['chroma']['persist_dir'],
            'embed_model': self.embed_model
        }
    
    # ========== Hook 相关方法 ==========
    
    def start_session(self, session_id: str):
        """会话开始 - 自动注入相关记忆"""
        self.current_session_id = session_id
        self.turn_count = 0
        self.pending_memories = []
    
    def end_session(self):
        """会话结束 - 保存待写入记忆"""
        if self.pending_memories and self.auto_save:
            self._flush_pending()
        self.current_session_id = None
        self.turn_count = 0
    
    def on_turn_end(self, user_msg: str, assistant_msg: str):
        """每轮对话结束 - 保存原文轮次 + 提取关键事实"""
        self.turn_count += 1
        
        # 1. 始终保存原文轮次（方案 A：保证有数据入库）
        if user_msg or assistant_msg:
            self.pending_memories.append({
                'content': f"User: {user_msg}\nAssistant: {assistant_msg}",
                'metadata': {
                    'type': 'raw_turn',
                    'source': 'chat',
                    'session_id': self.current_session_id,
                    'turn': self.turn_count
                }
            })
        
        # 2. 额外提取关键事实（保留原有逻辑，作为高价值标记）
        facts = self._extract_facts(user_msg, assistant_msg)
        for fact in facts:
            self.pending_memories.append({
                'content': fact,
                'metadata': {
                    'type': 'fact',
                    'source': 'chat',
                    'session_id': self.current_session_id,
                    'turn': self.turn_count
                }
            })
        
        # 定期刷新
        if self.turn_count % self.save_every_n == 0:
            self._flush_pending()
        
        # 检查是否需要压缩
        if self.compression_enabled and self.turn_count >= self.trigger_turns:
            self._maybe_compress()
    
    def _extract_facts(self, user_msg: str, assistant_msg: str) -> List[str]:
        """从对话中提取关键事实（简化版：基于关键词）"""
        facts = []
        combined = f"User: {user_msg}\nAssistant: {assistant_msg}"
        
        # 简单的关键词触发（实际可接入小模型做更好的抽取）
        triggers = ['偏好', '喜欢', '不喜欢', '习惯', '决定', '选择', '配置', '设置',
                    'prefer', 'like', 'dislike', 'habit', 'decide', 'choose', 'config', 'setting']
        
        for trigger in triggers:
            if trigger in combined.lower():
                # 取包含关键词的句子
                for sent in combined.split('。'):
                    if trigger in sent.lower() and len(sent) > 10:
                        facts.append(sent.strip() + '。')
                break
        
        return facts[:3]  # 每轮最多3条
    
    def _flush_pending(self):
        """批量写入待存记忆"""
        for mem in self.pending_memories:
            try:
                self.add(mem['content'], mem['metadata'])
            except Exception as e:
                print(f"[Memory-Local] Write failed: {e}")
        self.pending_memories.clear()
    
    def _maybe_compress(self):
        """检查并压缩旧记忆"""
        if not self.compression_enabled:
            return
        
        cutoff_date = datetime.now() - timedelta(days=self.keep_raw_days)
        cutoff_str = cutoff_date.isoformat()
        
        # 查询需要压缩的旧记忆（按会话分组）
        all_mem = self.collection.get(include=['documents', 'metadatas'])
        
        sessions_to_compress = {}
        for i, meta in enumerate(all_mem.get('metadatas', [])):
            created = meta.get('created_at', '')
            if created < cutoff_str and meta.get('type') == 'fact':
                sid = meta.get('session_id', 'unknown')
                if sid not in sessions_to_compress:
                    sessions_to_compress[sid] = []
                sessions_to_compress[sid].append({
                    'id': all_mem['ids'][i],
                    'content': all_mem['documents'][i],
                    'metadata': meta
                })
        
        # 对每个旧会话生成摘要
        for sid, mems in sessions_to_compress.items():
            if len(mems) < 3:  # 太少不压缩
                continue
            self._compress_session(sid, mems)
    
    def _compress_session(self, session_id: str, memories: List[Dict]):
        """压缩单个会话的记忆为摘要"""
        # 构建压缩提示
        content = "\n".join([f"- {m['content']}" for m in memories])
        prompt = f"""请将以下对话记忆压缩为一段不超过{self.summary_max_chars}字的摘要，保留关键事实、偏好、决定：

{content}

摘要："""
        
        try:
            # 调用本地小模型生成摘要
            resp = self.ollama_client.chat(
                model=self.summary_model,
                messages=[{'role': 'user', 'content': prompt}],
                options={'temperature': 0.3, 'num_predict': self.summary_max_chars}
            )
            summary = resp['message']['content'].strip()
            
            # 删除原始记忆
            ids_to_delete = [m['id'] for m in memories]
            self.collection.delete(ids=ids_to_delete)
            
            # 写入摘要
            self.add(
                content=f"[会话摘要] {summary}",
                metadata={
                    'type': 'summary',
                    'source': 'compression',
                    'session_id': session_id,
                    'original_count': len(memories),
                    'compressed_at': datetime.now().isoformat()
                }
            )
        except Exception as e:
            print(f"[Memory-Local] Compression failed for {session_id}: {e}")
    
    def inject_relevant_memories(self, user_input: str) -> str:
        """
        根据用户输入检索相关记忆，格式化为 system prompt 注入块
        """
        if not self.auto_inject:
            return ""
        
        memories = self.search(query=user_input, top_k=self.top_k, min_score=self.min_score)
        
        if not memories:
            return ""
        
        # 格式化注入内容
        lines = ["=== RELEVANT MEMORIES (auto-injected) ==="]
        total_chars = 0
        for mem in memories:
            entry = f"- [{mem['metadata'].get('type', 'fact')}] {mem['content']} (score: {mem['score']})"
            if total_chars + len(entry) > self.max_context_chars:
                break
            lines.append(entry)
            total_chars += len(entry)
        lines.append("=== END MEMORIES ===")
        
        return "\n".join(lines)


# 全局单例
_memory_store = None

def get_memory_store() -> MemoryStore:
    global _memory_store
    if _memory_store is None:
        _memory_store = MemoryStore()
    return _memory_store