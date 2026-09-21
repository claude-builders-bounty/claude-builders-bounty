import importlib.util, pathlib
path=pathlib.Path(__file__).parent/'.claude/hooks/block_destructive.py'
spec=importlib.util.spec_from_file_location('hook',path); mod=importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
blocked=[
 'rm -rf build', 'DROP TABLE users', 'git push origin main --force', 'git push -f origin main',
 'TRUNCATE TABLE sessions', 'DELETE FROM sessions', 'echo ok; DELETE FROM users; echo done'
]
allowed=['rm file.txt','git push origin main','DELETE FROM users WHERE id = 1','SELECT * FROM users','npm test','truncate -s 0 file.txt']
for cmd in blocked: assert mod.find_reason(cmd), cmd
for cmd in allowed: assert mod.find_reason(cmd) is None, (cmd,mod.find_reason(cmd))
print('ok')
