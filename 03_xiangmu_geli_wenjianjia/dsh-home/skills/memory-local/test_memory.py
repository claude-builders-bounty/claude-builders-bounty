import sys
sys.path.insert(0, '/home/user01/.hermes/skills/memory/memory-local')

from scripts.memory_core import get_memory_store

mem = get_memory_store()
print('Store initialized:', mem.collection.count(), 'memories')
print('Embed test:', len(mem._embed('test')))
print('Config:', mem.config['chroma']['persist_dir'])