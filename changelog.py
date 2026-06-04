#!/usr/bin/env python3
"""Generate CHANGELOG.md from git history."""
import subprocess, sys, re
from collections import defaultdict
CATS = [("feat","Added"),("fix","Fixed"),("change","Changed"),("remove","Removed")]
PATS = [(r"^(feat|feature)[:\(]","feat"),(r"^fix[:\(]","fix"),(r"^change[:\(]","change"),(r"^(remove|deprecate)","remove")]
def get_tag():
  r = subprocess.run(["git","describe","--tags","--abbrev=0"],capture_output=True,text=True)
  return r.stdout.strip() if r.returncode==0 else None
def get_commits(tag=None):
  cmd = ["git","log","--oneline","--format=%H%n%s%n%b---"]
  if tag: cmd.insert(2,f"{tag}..HEAD")
  r = subprocess.run(cmd,capture_output=True,text=True)
  commits = []
  for block in r.stdout.split("\n---\n"):
    lines = block.strip().split("\n")
    if len(lines)>=2: commits.append({"sha":lines[0][:7],"subject":lines[1]})
  return commits
def categorize(s):
  for p,c in PATS:
    if re.match(p,s,re.I): return c
  return "other"
def gen(commits):
  cats = defaultdict(list)
  for c in commits:
    cat = categorize(c["subject"])
    m = re.match(r"^\w+(\([^)]+\))?[!]?[:\(]\s*(.+)",c["subject"])
    desc = m.group(2) if m else c["subject"]
    cats[cat].append(f"- {desc} ({c['sha']})")
  lines = ["# Changelog",""]
  tag = get_tag()
  lines.append(f"## [{tag}]" if tag else "## [Unreleased]")
  lines.append("")
  for key,label in CATS:
    if cats.get(key):
      lines.append(f"### {label}")
      lines.extend(cats[key])
      lines.append("")
  return "\n".join(lines)
def main():
  tag = get_tag()
  commits = get_commits(tag)
  cl = gen(commits)
  with open("CHANGELOG.md","w") as f: f.write(cl+"\n")
  print(f"Generated CHANGELOG.md ({len(commits)} commits)")
if __name__ == "__main__": main()
