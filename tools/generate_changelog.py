#!/usr/bin/env python3
import argparse, re, subprocess
from collections import defaultdict
CATS = [('Added', r'^(feat|add|new)|\badd(ed)?\b'),('Fixed', r'^(fix|bug)|\bfix(ed)?\b'),('Changed', r'^(change|refactor|perf|improve)|\b(change|update|refactor|improve)d?\b'),('Removed', r'^(remove|delete)|\b(remove|delete)d?\b')]
def sh(args): return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL).strip()
def commits():
  try: tag = sh(['git','describe','--tags','--abbrev=0'])
  except Exception: tag = ''
  rng = f'{tag}..HEAD' if tag else 'HEAD'
  raw = sh(['git','log', rng, '--pretty=format:%s'])
  return [x.strip() for x in raw.splitlines() if x.strip()]
def cat(msg):
  low=msg.lower()
  for name, rx in CATS:
    if re.search(rx, low): return name
  return 'Changed'
def render(rows):
  grouped=defaultdict(list)
  for m in rows: grouped[cat(m)].append(m)
  out=['# Changelog','','## Unreleased','']
  for name,_ in CATS:
    out += [f'### {name}'] + [f'- {m}' for m in grouped.get(name, ['No entries.'])] + ['']
  return '\n'.join(out).rstrip()+'\n'
def main():
  ap=argparse.ArgumentParser(); ap.add_argument('-o','--output',default='CHANGELOG.md'); ns=ap.parse_args()
  open(ns.output,'w',encoding='utf-8').write(render(commits()))
if __name__=='__main__': main()
