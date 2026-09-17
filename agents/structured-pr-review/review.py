#!/usr/bin/env python3
"""Fetch a pinned GitHub PR and print a structured Claude Code review."""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import time
from typing import Any

ROOT=Path(__file__).resolve().parent
SCHEMA={"type":"object","additionalProperties":False,"required":["summary","risks","suggestions","confidence"],"properties":{
 "summary":{"type":"string","minLength":1},
 "risks":{"type":"array","items":{"type":"object","additionalProperties":False,"required":["path","line","severity","description"],"properties":{"path":{"type":["string","null"]},"line":{"type":["integer","null"],"minimum":1},"severity":{"type":"string","enum":["low","medium","high"]},"description":{"type":"string","minLength":1}}}},
 "suggestions":{"type":"array","items":{"type":"string","minLength":1}},
 "confidence":{"type":"string","enum":["Low","Medium","High"]}}}
class ReviewError(Exception):pass

def command(args:list[str],*,stdin:str|None=None,cwd:Path|None=None,timeout:int=60)->str:
 try:r=subprocess.run(args,input=stdin,cwd=cwd,text=True,encoding='utf-8',errors='replace',stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout,check=False,env={**os.environ,'GH_PAGER':'cat','PAGER':'cat','GH_PROMPT_DISABLED':'1'})
 except (OSError,subprocess.TimeoutExpired) as exc:raise ReviewError(f'{args[0]} could not complete: {exc}') from exc
 if r.returncode:
  detail=(r.stderr or r.stdout).strip().splitlines()
  message=detail[-1][:500] if detail else 'no diagnostic'
  try:
   envelope=json.loads(r.stdout)
   if isinstance(envelope,dict) and isinstance(envelope.get('result'),str):message=envelope['result'][:1000]
  except (ValueError,TypeError):pass
  failure=ReviewError(f'{args[0]} exited {r.returncode}: '+message)
  failure.diagnostics={'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr}
  raise failure
 return r.stdout

def parse_pr(value:str)->tuple[str,int]:
 match=re.fullmatch(r'https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/pull/([1-9]\d*)/?',value)
 if not match or any(s in {'.','..'} for s in match.groups()[:2]):raise ReviewError('Use an exact https://github.com/OWNER/REPO/pull/NUMBER URL')
 return f'{match[1]}/{match[2]}',int(match[3])

def api(endpoint:str)->Any:
 try:return json.loads(command(['gh','api',endpoint]))
 except ValueError as exc:raise ReviewError('GitHub returned invalid JSON') from exc

def collect(url:str,max_bytes:int)->dict[str,Any]:
 repo,number=parse_pr(url);endpoint=f'repos/{repo}/pulls/{number}';before=api(endpoint)
 if not isinstance(before,dict) or not isinstance(before.get('head'),dict):raise ReviewError('GitHub PR metadata is incomplete')
 sha=before['head'].get('sha')
 if not isinstance(sha,str) or not re.fullmatch(r'[0-9a-f]{40}',sha):raise ReviewError('Missing valid PR head SHA')
 count=before.get('changed_files')
 if not isinstance(count,int) or count<0 or count>3000:raise ReviewError('Cannot establish complete GitHub changed-file coverage')
 files=[]
 for page in range(1,(count+99)//100+1):
  rows=api(endpoint+f'/files?per_page=100&page={page}')
  if not isinstance(rows,list):raise ReviewError('GitHub changed-files response is invalid')
  files.extend(rows)
 if len(files)!=count:raise ReviewError('Changed-file pagination is incomplete; no review generated')
 if len({x.get('filename') for x in files})!=count:raise ReviewError('Duplicate or invalid changed-file entry')
 normalized=[];limits=[];total=0
 for f in files:
  patch=f.get('patch');path=f.get('filename')
  if not isinstance(path,str) or not path:raise ReviewError('Missing changed path')
  if patch is None:
   limits.append(f'No textual patch supplied by GitHub for {path}; binary, empty or omitted patch')
  elif not isinstance(patch,str):raise ReviewError('Invalid patch type')
  else:total+=len(patch.encode('utf-8'))
  normalized.append({'path':path,'status':f.get('status'),'previous_path':f.get('previous_filename'),'additions':f.get('additions'),'deletions':f.get('deletions'),'patch':patch})
 if total>max_bytes:raise ReviewError(f'Diff exceeds {max_bytes} bytes; split the PR or raise --max-diff-bytes explicitly')
 after=api(endpoint)
 if after.get('head',{}).get('sha')!=sha or after.get('changed_files')!=count:raise ReviewError('PR changed while collecting; retry a stable revision')
 return {'url':url.rstrip('/'),'repository':repo,'number':number,'title':before.get('title',''),'description':str(before.get('body') or '')[:6000],'head_sha':sha,'base_sha':before.get('base',{}).get('sha'),'files':normalized,'limitations':limits,'tests_executed':False}

def decode_response(text:str)->tuple[dict[str,Any],dict[str,Any]]:
 try:envelope=json.loads(text)
 except ValueError as exc:raise ReviewError('Claude CLI did not return valid JSON') from exc
 if not isinstance(envelope,dict):raise ReviewError('Claude CLI response must be an object')
 if envelope.get('is_error') or envelope.get('subtype','').startswith('error'):raise ReviewError('Claude CLI reported an error; no review accepted')
 data=envelope.get('structured_output')
 if data is None:
  result=envelope.get('result')
  if not isinstance(result,str):raise ReviewError('Claude CLI returned neither structured_output nor result')
  candidate=result.strip()
  fenced=re.fullmatch(r'```(?:json)?\s*\n([\s\S]*?)\n```',candidate,flags=re.I)
  if fenced:candidate=fenced.group(1)
  try:data=json.loads(candidate)
  except ValueError as exc:raise ReviewError('Claude review text is not one JSON object or one JSON code block') from exc
 return data,{k:envelope.get(k) for k in ['duration_ms','total_cost_usd','num_turns','modelUsage'] if k in envelope}

def validate(review:Any,packet:dict[str,Any])->dict[str,Any]:
 if not isinstance(review,dict) or set(review)!=set(SCHEMA['required']):raise ReviewError('Review does not match required fields')
 if not isinstance(review['summary'],str) or not review['summary'].strip():raise ReviewError('Review summary is missing')
 if review['confidence'] not in ['Low','Medium','High']:raise ReviewError('Invalid confidence value')
 if not isinstance(review['risks'],list) or not isinstance(review['suggestions'],list):raise ReviewError('Risks and suggestions must be arrays')
 paths={f['path'] for f in packet['files']}
 for finding in review['risks']:
  if not isinstance(finding,dict) or set(finding)!={'path','line','severity','description'}:raise ReviewError('Malformed risk record')
  if finding['path'] is not None and finding['path'] not in paths:raise ReviewError('Risk cites a path outside the collected diff')
  line=finding['line']
  if line is not None and (type(line) is not int or line<1):raise ReviewError('Risk has an invalid new-side line')
  if finding['severity'] not in ['low','medium','high'] or not isinstance(finding['description'],str) or not finding['description'].strip():raise ReviewError('Risk evidence or severity is invalid')
  # Validate line references against actual new-side hunk coverage.
  if line is not None:
   if finding['path'] is None:raise ReviewError('A line reference requires a path')
   patch=next(f['patch'] for f in packet['files'] if f['path']==finding['path']) or ''
   ranges=[(int(a),int(b or 1)) for a,b in re.findall(r'^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@',patch,re.M)]
   if not any(start<=line<start+length for start,length in ranges):raise ReviewError('Risk line is outside supplied new-side hunks')
 for item in review['suggestions']:
  if not isinstance(item,str) or not item.strip():raise ReviewError('Suggestion must be a nonempty string')
 if packet['limitations'] and review['confidence']=='High':raise ReviewError('High confidence is invalid when textual patches are missing')
 return review

def escape(text:str)->str:
 text=html.escape(' '.join(text.split()),quote=False)
 return re.sub(r'([\\`*_{}\[\]()#+!|>])',r'\\\1',text)

def render(review:dict[str,Any],packet:dict[str,Any])->str:
 lines=['# Pull request review','',f"Source: {packet['url']}",f"Reviewed head: `{packet['head_sha']}`",'', '## Summary','',escape(review['summary']),'','## Identified risks','']
 if not review['risks']:lines.append('- No specific defect established from the supplied diff; this is not proof of absence.')
 for r in review['risks']:
  where=escape(r['path']) if r['path'] else 'Diff-wide'
  if r['line'] is not None:where+=':'+str(r['line'])
  lines.append(f"- **{r['severity'].capitalize()}** | {where}: {escape(r['description'])}")
 lines+=['','## Improvement suggestions','']
 lines += ['- '+escape(s) for s in review['suggestions']] or ['- No additional suggestions grounded in this diff.']
 lines+=['','## Confidence','',review['confidence'],'','## Evidence limits','','Diff-only review; no repository code, build, or tests were executed by this tool.']
 lines+=['- '+escape(x) for x in packet['limitations']]
 return '\n'.join(lines)+'\n'

def infer(packet:dict[str,Any],model:str,timeout:int,budget:float,backend:str="claude")->tuple[dict[str,Any],dict[str,Any]]:
 from grounding import grounded_infer
 local=None
 if backend=='ollama':
  from ollama_backend import infer_json
  local=lambda stage,system,payload,schema:infer_json(stage,system,payload,schema,model,timeout)
 result,metadata=grounded_infer(packet,model,timeout,budget,command,decode_response,validate,ReviewError,local)
 metadata['backend']=backend
 metadata['claude_code_used']=backend=='claude'
 return result,metadata

def main(argv:list[str]|None=None)->int:
 parser=argparse.ArgumentParser(description=__doc__)
 parser.add_argument('--pr',required=True,help='Exact public/private GitHub PR URL accessible through gh')
 parser.add_argument('--backend',choices=['claude','ollama'],default='claude',help='Claude Code by default; direct-local Ollama is a distinct optional backend')
 parser.add_argument('--model',default='opus',help='Claude Code model (default: opus, the validated profile; selectable)')
 parser.add_argument('--timeout',type=int,default=180)
 parser.add_argument('--max-budget-usd',type=float,default=1.0)
 parser.add_argument('--max-diff-bytes',type=int,default=150000)
 parser.add_argument('--evidence-dir',type=Path,help='Create a NEW directory with the exact input/review hashes and metadata')
 parser.add_argument('--collect-only',action='store_true',help='Output the pinned JSON packet without calling Claude')
 args=parser.parse_args(argv)
 evidence_started=False
 try:
  if args.timeout<1 or args.max_diff_bytes<1 or not 0<args.max_budget_usd<=100:raise ReviewError('Limits must be positive; maximum single-run budget is $100')
  if args.evidence_dir and args.evidence_dir.exists():raise ReviewError('Evidence directory already exists; select a new directory to preserve prior runs')
  started=time.time();packet=collect(args.pr,args.max_diff_bytes)
  if args.collect_only:
   print(json.dumps(packet,indent=2,ensure_ascii=False));return 0
  if args.evidence_dir:
   args.evidence_dir.mkdir(parents=True,exist_ok=False);evidence_started=True
   (args.evidence_dir/'input.json').write_text(json.dumps(packet,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
  review,provider=infer(packet,args.model,args.timeout,args.max_budget_usd,args.backend)
  rendered=render(review,packet)
  if provider.get('grounding_notes'):
   rendered+='\n## Verification notes\n\n'+'\n'.join('- '+escape(x) for x in provider['grounding_notes'])+'\n'
  if args.evidence_dir:
   input_bytes=json.dumps(packet,indent=2,ensure_ascii=False).encode('utf-8')
   (args.evidence_dir/'input.json').write_bytes(input_bytes)
   (args.evidence_dir/'verification.json').write_text(json.dumps(provider,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
   (args.evidence_dir/'review.json').write_text(json.dumps(review,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
   (args.evidence_dir/'review.md').write_text(rendered,encoding='utf-8')
   receipt={'url':packet['url'],'head_sha':packet['head_sha'],'model_requested':args.model,'duration_seconds':round(time.time()-started,3),'input_sha256':hashlib.sha256(input_bytes).hexdigest(),'review_sha256':hashlib.sha256(rendered.encode()).hexdigest(),'provider_metadata':provider,'tests_executed':False,'posted_to_github':False}
   (args.evidence_dir/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
  sys.stdout.write(rendered);return 0
 except (ReviewError,OSError,ValueError,KeyError) as exc:
  if evidence_started:
   error={'error':str(exc),'success':False,'provider_response':getattr(exc,'raw_response',None),'diagnostics':getattr(exc,'diagnostics',None)}
   try:(args.evidence_dir/'error.json').write_text(json.dumps(error,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
   except OSError:pass
  print(f'claude-review: {exc}',file=sys.stderr);return 2

if __name__=='__main__':raise SystemExit(main())
