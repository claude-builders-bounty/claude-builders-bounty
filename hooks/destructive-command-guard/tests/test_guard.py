import importlib.util,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('guard',ROOT/'guard.py');g=importlib.util.module_from_spec(spec);spec.loader.exec_module(g)
BLOCK=[
 'rm -rf /fixture','rm -fr /fixture','rm -r -f /fixture','rm --recursive --force /fixture','/bin/rm -Rf /fixture','sudo -u nobody rm -rf /fixture','env MODE=test rm -rf /fixture','command rm -rf /fixture','echo hello && rm -rf /fixture','git push --force origin main','git -C /fixture push -f origin main','git push origin +main:main','bash -c "rm -rf /fixture"','sh -lc "git push --force"','DROP TABLE users;','TRUNCATE TABLE users;','DELETE FROM users;','psql -c "DROP TABLE users;"','sqlite3 test.db "TRUNCATE users;"','mysql -e "DELETE FROM users;"',
 "psql -c \"DELETE FROM users RETURNING 'WHERE';\"",'psql -c "DELETE FROM users /* WHERE id=1 */;"','psql -c "DELETE FROM users USING (SELECT id FROM other WHERE active=1) nested;"','psql -c "DELETE FROM first WHERE id=1; DELETE FROM second;"','find . -exec rm -rf {} +','printf "DELETE FROM users;" | psql',
]
ALLOW=[
 'git status','git push origin main','git push --force-with-lease origin main','rm file.txt','rm -r folder','rm -f file','rm -- -rf','echo "rm -rf /fixture"','printf "DROP TABLE users;"','python3 -m unittest','npm run build','ls -la','echo hello # rm -rf /fixture',
 'psql -c "DELETE FROM users WHERE id=1;"',"psql -c \"SELECT 'DROP TABLE users';\"",'psql -c "SELECT * FROM users;"','psql -c "DELETE FROM users WHERE id IN (SELECT id FROM old WHERE inactive=1);"','psql -c "-- DELETE FROM users;\nSELECT 1;"','sqlite3 db "SELECT 1 /* DROP TABLE users */;"','git push --follow-tags origin main','echo "DELETE FROM users;"',
]
class Classification(unittest.TestCase):pass
for i,command in enumerate(BLOCK):
 def blocked(self,command=command):self.assertTrue(g.inspect(command),command)
 setattr(Classification,f'test_block_{i:02}',blocked)
for i,command in enumerate(ALLOW):
 def allowed(self,command=command):self.assertEqual(g.inspect(command),[],command)
 setattr(Classification,f'test_allow_{i:02}',allowed)
class Protocol(unittest.TestCase):
 def setUp(self):self.tmp=tempfile.TemporaryDirectory();self.home=Path(self.tmp.name);self.env={**os.environ,'HOME':str(self.home)}
 def tearDown(self):self.tmp.cleanup()
 def call(self,event):return subprocess.run([sys.executable,str(ROOT/'guard.py')],input=json.dumps(event),capture_output=True,text=True,env=self.env,timeout=5)
 def test_deny_and_log(self):
  cmd='rm -rf /nonexistent-fixture-only';r=self.call({'tool_name':'Bash','tool_input':{'command':cmd},'cwd':'/fixture/project'})
  self.assertEqual(r.returncode,0);self.assertEqual(json.loads(r.stdout)['hookSpecificOutput']['permissionDecision'],'deny')
  p=self.home/'.claude/hooks/blocked.log';d=json.loads(p.read_text());self.assertEqual(d['command'],cmd);self.assertEqual(d['project_path'],'/fixture/project');self.assertIn('+00:00',d['timestamp']);self.assertEqual(p.stat().st_mode&0o777,0o600)
 def test_safe_request_does_not_log(self):
  r=self.call({'tool_name':'Bash','tool_input':{'command':'git status'},'cwd':'/fixture'})
  self.assertEqual(json.loads(r.stdout),{});self.assertFalse((self.home/'.claude').exists())
 def test_non_bash_ignored(self):self.assertEqual(json.loads(self.call({'tool_name':'Read','tool_input':{'file_path':'rm -rf'}}).stdout),{})
 def test_log_keeps_two_attempts(self):
  e={'tool_name':'Bash','tool_input':{'command':'git push --force'},'cwd':'/fixture'};self.call(e);self.call(e);self.assertEqual(len((self.home/'.claude/hooks/blocked.log').read_text().splitlines()),2)
 def test_log_symlink_does_not_write_target(self):
  h=self.home/'.claude/hooks';h.mkdir(parents=True);p=self.home/'target';p.write_text('keep');(h/'blocked.log').symlink_to(p)
  r=self.call({'tool_name':'Bash','tool_input':{'command':'rm -rf /fixture'}});self.assertIn('audit log',json.loads(r.stdout)['hookSpecificOutput']['permissionDecisionReason']);self.assertEqual(p.read_text(),'keep')
 def test_malformed_input_explained(self):
  r=subprocess.run([sys.executable,str(ROOT/'guard.py')],input='{',capture_output=True,text=True,env=self.env)
  self.assertEqual(json.loads(r.stdout)['hookSpecificOutput']['permissionDecision'],'deny')
 def test_quoted_shell_parse_error_explained(self):
  r=self.call({'tool_name':'Bash','tool_input':{'command':'echo "unterminated'}});self.assertIn('Cannot inspect',json.loads(r.stdout)['hookSpecificOutput']['permissionDecisionReason'])
 def test_installer_preserves_existing_settings_and_is_idempotent(self):
  c=self.home/'config with spaces';c.mkdir();(c/'settings.json').write_text(json.dumps({'env':{'DEMO':'preserve'},'hooks':{'PostToolUse':[{'matcher':'Read','hooks':[]}]}}))
  for _ in range(2):
   r=subprocess.run([sys.executable,str(ROOT/'install.py'),'--config-dir',str(c)],capture_output=True,text=True);self.assertEqual(r.returncode,0,r.stderr)
  d=json.loads((c/'settings.json').read_text());self.assertEqual(d['env']['DEMO'],'preserve');self.assertEqual(len(d['hooks']['PreToolUse']),1);self.assertIn('PostToolUse',d['hooks'])
 def test_installer_refuses_malformed_settings(self):
  c=self.home/'config';c.mkdir();(c/'settings.json').write_text('{broken')
  r=subprocess.run([sys.executable,str(ROOT/'install.py'),'--config-dir',str(c)],capture_output=True,text=True);self.assertEqual(r.returncode,2);self.assertEqual((c/'settings.json').read_text(),'{broken')
if __name__=='__main__':unittest.main()
