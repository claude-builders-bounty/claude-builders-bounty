import json, subprocess, sys
import os
hook=os.path.join(os.path.dirname(__file__),'pre_tool_use_blocker.py')
cases=[('rm -rf /tmp/x',2),('DELETE FROM users',2),('DELETE FROM users WHERE id=1',0),('echo ok',0),('git push --force origin main',2)]
for cmd,exp in cases:
 p=subprocess.run([hook],input=json.dumps({'tool_input':{'command':cmd}}),text=True,capture_output=True)
 assert p.returncode==exp,(cmd,p.returncode,p.stderr)
print('ok')
