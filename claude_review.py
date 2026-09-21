#!/usr/bin/env python3
import argparse, subprocess, sys

def sh(args): return subprocess.check_output(args, text=True, stderr=subprocess.STDOUT)
def analyze(diff):
  files=[line[10:] for line in diff.splitlines() if line.startswith('diff --git')]
  risks=[]
  if any('package-lock' in f or 'pnpm-lock' in f for f in files): risks.append('Dependency lockfile changed; review dependency intent.')
  if any('/api/' in f or 'server' in f.lower() for f in files): risks.append('Server/API code changed; verify auth, validation, and error handling.')
  if not risks: risks.append('No obvious high-risk file patterns detected from the diff metadata.')
  suggestions=['Add or update tests for changed behavior.','Keep the PR focused and document any migration or config changes.']
  confidence='Medium' if len(diff) > 2000 else 'Low'
  return '\n'.join(['## PR Review','','### Summary',f'This PR changes {len(files)} file(s). Review focuses on diff metadata and common risk patterns.','','### Identified risks']+[f'- {r}' for r in risks]+['','### Improvement suggestions']+[f'- {s}' for s in suggestions]+['',f'### Confidence: {confidence}',''])
def main():
  ap=argparse.ArgumentParser(); ap.add_argument('--pr', required=True); ns=ap.parse_args()
  diff=sh(['gh','pr','diff',ns.pr])
  print(analyze(diff))
if __name__=='__main__': main()
