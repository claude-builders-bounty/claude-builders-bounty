import json, os, subprocess, sys, unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from pre_tool_use_hook import evaluate
ROOT = Path(__file__).parent
class HookTests(unittest.TestCase):
    def test_dangerous_patterns(self):
        cases = ['rm -rf build','rm -fr build','rm -r -f build','/bin/rm --recursive --force build','sudo rm -rf build','git push --force origin main','git -C repo push -f origin main','git push origin main --force-with-lease','DROP TABLE users','TRUNCATE TABLE users','DELETE FROM users','DELETE FROM users WHERE id=1; DELETE FROM secrets',"DELETE FROM users /* WHERE id=1 */", "DELETE FROM users WHERE name='x'; DELETE FROM secrets WHERELESS"]
        for command in cases:
            with self.subTest(command=command): self.assertTrue(evaluate(command)[0])
    def test_normal_patterns(self):
        cases = ['rm file.txt','git push origin main','git push origin main --force-if-includes','git log --oneline','python3 -m unittest',"echo 'rm -rf build'",'DELETE FROM users WHERE id=1', "SELECT 'DROP TABLE users'",'echo TRUNCATE','rm --force file.txt','rm --recursive directory']
        for command in cases:
            with self.subTest(command=command): self.assertFalse(evaluate(command)[0])
    def run_hook(self, payload, home):
        return subprocess.run([sys.executable,str(ROOT/'pre_tool_use_hook.py')],input=json.dumps(payload),text=True,capture_output=True,env={**os.environ,'HOME':home})
    def test_cli_deny_and_log(self):
        with TemporaryDirectory(dir=os.environ.get('HOOK_TEST_TMPDIR')) as home:
            p=self.run_hook({'tool_name':'Bash','tool_input':{'command':'rm -rf NEVER_EXECUTED'},'cwd':'/synthetic/project'},home)
            self.assertEqual(p.returncode,0)
            self.assertEqual(json.loads(p.stdout)['hookSpecificOutput']['permissionDecision'],'deny')
            record=json.loads((Path(home)/'.claude/hooks/blocked.log').read_text())
            self.assertEqual(record['project_path'],'/synthetic/project')
            self.assertEqual(record['attempted_command'],'rm -rf NEVER_EXECUTED')
            self.assertIn('timestamp',record)
    def test_cli_normal_defers_permission(self):
        with TemporaryDirectory(dir=os.environ.get('HOOK_TEST_TMPDIR')) as home:
            p=self.run_hook({'tool_name':'Bash','tool_input':{'command':'git status'}},home)
            self.assertEqual(p.returncode,0);self.assertEqual(p.stdout,'')
            self.assertFalse((Path(home)/'.claude/hooks/blocked.log').exists())
    def test_non_bash_ignored(self):
        with TemporaryDirectory(dir=os.environ.get('HOOK_TEST_TMPDIR')) as home:
            p=self.run_hook({'tool_name':'Write','tool_input':{'command':'rm -rf never'}},home)
            self.assertEqual(p.stdout,'');self.assertEqual(p.returncode,0)
    def test_malformed_input_blocks(self):
        p=subprocess.run([sys.executable,str(ROOT/'pre_tool_use_hook.py')],input='{',text=True,capture_output=True)
        self.assertEqual(p.returncode,2);self.assertIn('Invalid hook input',p.stderr)
if __name__=='__main__':unittest.main()
