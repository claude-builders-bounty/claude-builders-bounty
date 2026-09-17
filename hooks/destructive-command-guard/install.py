#!/usr/bin/env python3
"""Install this opt-in hook into a user-selected Claude configuration directory."""
import argparse,json,os,shlex,sys,tempfile
from pathlib import Path

def atomic(path,data):
 with tempfile.NamedTemporaryFile(dir=path.parent,prefix='.hook-install-',delete=False) as f:
  tmp=Path(f.name)
  try:f.write(data);f.flush();os.fsync(f.fileno());os.chmod(tmp,0o600);os.replace(tmp,path)
  finally:
   if tmp.exists():tmp.unlink()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config-dir',type=Path,default=Path.home()/'.claude');args=p.parse_args()
 root=args.config_dir.expanduser().absolute();settings=root/'settings.json';target=root/'hooks/destructive-command-guard.py'
 try:
  if settings.is_symlink() or target.is_symlink():raise ValueError('Use a regular-file configuration destination')
  old=settings.read_bytes() if settings.exists() else b'{}';data=json.loads(old)
  if not isinstance(data,dict):raise ValueError('Settings must be a JSON object')
  hooks=data.setdefault('hooks',{});pre=hooks.setdefault('PreToolUse',[])
  if not isinstance(hooks,dict) or not isinstance(pre,list):raise ValueError('Existing hook settings have an unexpected shape')
  source=(Path(__file__).resolve().parent/'guard.py').read_bytes()
  if target.exists() and target.read_bytes()!=source:raise ValueError('Existing installed hook differs; review it before replacing it')
  command='python3 '+shlex.quote(str(target))+' --log-file '+shlex.quote(str(root/'hooks/blocked.log'))
  entry={'matcher':'Bash','hooks':[{'type':'command','command':command,'timeout':5}]}
  if not any(e==entry for e in pre):pre.append(entry)
  root.mkdir(parents=True,exist_ok=True,mode=0o700);target.parent.mkdir(exist_ok=True,mode=0o700)
  atomic(target,source)
  # Do not overwrite a concurrent settings edit.
  if (settings.read_bytes() if settings.exists() else b'{}')!=old:raise ValueError('Settings changed during install; review before retrying')
  atomic(settings,(json.dumps(data,indent=2)+'\n').encode())
  print('Installed one Bash PreToolUse hook in '+str(settings));return 0
 except (OSError,ValueError,TypeError,AttributeError) as exc:
  print('Installation stopped: '+str(exc),file=sys.stderr);return 2
if __name__=='__main__':raise SystemExit(main())
