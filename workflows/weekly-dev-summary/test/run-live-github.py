#!/usr/bin/env python3
"""Run actual n8n against live public GitHub, with explicitly synthetic model/delivery."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import argparse,copy,datetime,hashlib,json,os,re,shutil,socket,subprocess,threading
ROOT=Path(__file__).resolve().parents[1];WORK=ROOT.parent
NODE=Path(os.environ.get('NODE_BIN') or str(WORK/'tool-home/node-v24.21.0-linux-x64/bin/node'))
CLI=Path(os.environ.get('N8N_CLI') or str(WORK/'tool-home/n8n-runtime/node_modules/n8n/bin/n8n'))
OUT=ROOT/'live-github-evidence'
POSTS=[]
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_POST(self):
  data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  POSTS.append({'path':self.path,'request':data})
  if self.path=='/messages':
   evidence=json.loads(data['messages'][0]['content'])
   response={'id':'synthetic-summary-of-live-github','type':'message','role':'assistant','content':[{'type':'text','text':'SYNTHETIC model response for live GitHub transport test. Counts: '+json.dumps(evidence['counts'])}],'stop_reason':'end_turn','model':data['model'],'usage':{'input_tokens':0,'output_tokens':0}}
  elif self.path.startswith('/discord'):
   assert data['allowed_mentions']=={'parse':[]};assert 0<len(data['content'])<=2000
   response={'id':'synthetic-local-delivery','content':data['content']}
  else:self.send_error(404);return
  raw=json.dumps(response).encode();self.send_response(200);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
def port():
 with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def main():
 global OUT
 ap=argparse.ArgumentParser(description=__doc__)
 ap.add_argument('--repository',default='octocat/Hello-World')
 ap.add_argument('--require-activity',action='store_true')
 args=ap.parse_args()
 if not re.fullmatch(r'[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+',args.repository):ap.error('Expected owner/repository')
 OUT=OUT/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');OUT.mkdir(parents=True,exist_ok=False)
 source=json.loads((ROOT/'workflow.json').read_text());wf=copy.deepcopy(source)
 wf['name']='LIVE GitHub collection / SYNTHETIC Claude and Discord';wf['id']='coffeeLiveGithub'+OUT.name
 server=ThreadingHTTPServer(('127.0.0.1',0),Handler);threading.Thread(target=server.serve_forever,daemon=True).start();base=f'http://127.0.0.1:{server.server_port}'
 for n in wf['nodes']:
  p=n['parameters']
  if n['name']=='Configuration':p['jsCode']=p['jsCode'].replace("'octocat/Hello-World'",repr(args.repository)).replace('REPLACE/REPLACE','123456789/synthetic-test-only')
  if n['name'].startswith('GitHub '):p['authentication']='none';p.pop('genericAuthType',None)
  if n['name']=='Claude Summary':p['url']=base+'/messages';p['authentication']='none';p.pop('genericAuthType',None)
  if n['name']=='Deliver Discord':p['url']=base+'/discord'
 wfpath=OUT/'workflow.json';wfpath.write_text(json.dumps(wf,indent=2))
 env={'PATH':str(NODE.parent)+':/usr/bin:/bin','HOME':str(WORK/'tool-home'),'LANG':'C.UTF-8','TZ':'UTC','N8N_USER_FOLDER':str(WORK/'tool-home/n8n-state'),'N8N_DIAGNOSTICS_ENABLED':'false','N8N_VERSION_NOTIFICATIONS_ENABLED':'false','N8N_TEMPLATES_ENABLED':'false','N8N_PERSONALIZATION_ENABLED':'false','N8N_COMMUNITY_PACKAGES_ENABLED':'false','N8N_SECURE_COOKIE':'false','N8N_LOG_LEVEL':'warn','N8N_RUNNERS_MODE':'internal','N8N_RUNNERS_BROKER_PORT':str(port()),'N8N_PORT':str(port()),'NODE_OPTIONS':'--max-old-space-size=1536','NO_PROXY':'127.0.0.1,localhost'}
 record={'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'repo':args.repository,'github':'live public unauthenticated GitHub REST endpoints','anthropic':'synthetic local HTTP response','discord':'synthetic local HTTP delivery','source_sha256':hashlib.sha256((ROOT/'workflow.json').read_bytes()).hexdigest(),'passed':False}
 try:
  for name,cli_args in [('import',['import:workflow','--input',str(wfpath)]),('execute',['execute','--id',wf['id'],'--rawOutput'])]:
   r=subprocess.run([str(NODE),str(CLI)]+cli_args,env=env,cwd=ROOT,capture_output=True,text=True,timeout=240)
   (OUT/(name+'.stdout.log')).write_text(r.stdout);(OUT/(name+'.stderr.log')).write_text(r.stderr)
   record[name+'_exit']=r.returncode
   if r.returncode:print((r.stdout+r.stderr)[-3000:]);break
  else:
   model=[x for x in POSTS if x['path']=='/messages'];deliveries=[x for x in POSTS if x['path'].startswith('/discord')]
   assert len(model)==1 and len(deliveries)>=1
   evidence=json.loads(model[0]['request']['messages'][0]['content'])
   (OUT/'collected-evidence.json').write_text(json.dumps(evidence,indent=2))
   assert evidence['repo']==record['repo'] and all(isinstance(v,int) and v>=0 for v in evidence['counts'].values())
   if args.require_activity:assert sum(evidence['counts'].values())>0,'Expected at least one real activity item'
   record.update(passed=True,counts=evidence['counts'],local_delivery_count=len(deliveries))
 finally:
  server.shutdown();server.server_close();record['finished_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();(OUT/'result.json').write_text(json.dumps(record,indent=2));print(json.dumps(record),flush=True)
 return 0 if record['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
