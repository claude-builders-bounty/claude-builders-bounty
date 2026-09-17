#!/usr/bin/env python3
"""Exercise the real n8n engine against explicitly synthetic HTTP services."""
from pathlib import Path
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import argparse, copy, datetime, hashlib, json, os, shutil, socket, subprocess, threading
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT.parent
RUNTIME=WORK/'tool-home/n8n-runtime'
local_metadata=WORK/'tool-home/node-runtime.json'
node_default=str(Path(json.loads(local_metadata.read_text())['directory'])/'node') if local_metadata.exists() else shutil.which('node')
NODE_BINARY=Path(os.environ.get('NODE_BIN') or node_default or 'node')
NODE=NODE_BINARY.parent
local_cli=RUNTIME/'node_modules/n8n/bin/n8n'
N8N_CLI=Path(os.environ.get('N8N_CLI') or (str(local_cli) if local_cli.exists() else shutil.which('n8n') or 'n8n'))
OUT=ROOT/'engine-evidence'; OUT.mkdir(exist_ok=True)
STATE={'scenario':'normal-en','requests':[],'deliveries':[]}
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args): pass
    def respond(self,code,data,headers=None):
        raw=json.dumps(data).encode(); self.send_response(code)
        self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(raw)))
        for k,v in (headers or {}).items(): self.send_header(k,v)
        self.end_headers(); self.wfile.write(raw)
    def do_GET(self):
        p=urlparse(self.path); q=parse_qs(p.query); page=int(q.get('page',['1'])[0])
        STATE['requests'].append({'method':'GET','path':self.path})
        if p.path.endswith('/commits'):
            data=[] if STATE['scenario']=='empty' else [{'sha':'commit-'+str(page),'html_url':'https://github.com/fixture/repo/commit/'+str(page),'commit':{'message':'Synthetic test change '+str(page),'committer':{'date':'2026-09-15T10:00:00Z'}}}]
            headers={'Link':f'<http://127.0.0.1:{self.server.server_port}{p.path}?page=2>; rel="next"'} if page==1 and STATE['scenario']!='empty' else {}
            return self.respond(200,data,headers)
        if p.path=='/search/issues':
            ispr='is:pr' in q.get('q',[''])[0]
            items=[] if STATE['scenario']=='empty' else [{'number':2 if ispr else 1,'title':'Synthetic merged PR' if ispr else 'Synthetic closed issue','html_url':'https://github.com/fixture/repo/issues/1','closed_at':'2026-09-15T12:00:00Z',**({'pull_request':{'url':'https://api.github.com/repos/fixture/repo/pulls/2'}} if ispr else {})}]
            return self.respond(200,{'total_count':len(items),'incomplete_results':STATE['scenario']=='incomplete','items':items})
        return self.respond(404,{'error':'unknown synthetic endpoint'})
    def do_POST(self):
        raw=self.rfile.read(int(self.headers.get('Content-Length','0'))); data=json.loads(raw)
        STATE['requests'].append({'method':'POST','path':self.path,'body':data})
        if self.path=='/messages':
            assert data.get('model')=='claude-sonnet-4-6'
            evidence=json.loads(data['messages'][0]['content'])
            french='French' in data.get('system','')
            text=('Résumé synthétique de test. ' if french else 'Synthetic test summary. ')+json.dumps(evidence['counts'])
            return self.respond(200,{'id':'synthetic-message','type':'message','role':'assistant','model':data['model'],'content':[{'type':'text','text':text}],'stop_reason':'max_tokens' if STATE['scenario']=='truncated' else 'end_turn','usage':{'input_tokens':0,'output_tokens':0}})
        if self.path.startswith('/discord'):
            assert data.get('allowed_mentions')=={'parse':[]}
            assert 0<len(data['content'])<=2000
            STATE['deliveries'].append(data)
            return self.respond(200,{'id':'synthetic-discord-message','content':data['content']})
        return self.respond(404,{'error':'unknown synthetic endpoint'})
def free_port():
    with socket.socket() as s:s.bind(('127.0.0.1',0));return s.getsockname()[1]
def main():
    ap=argparse.ArgumentParser();ap.add_argument('scenarios',nargs='*',default=['normal-en','normal-fr','empty','incomplete','truncated']);args=ap.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',0),Handler);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    base=f'http://127.0.0.1:{server.server_port}'
    source=json.loads((ROOT/'workflow.json').read_text()); results=[]
    env={'PATH':str(NODE)+':/usr/bin:/bin','HOME':str(WORK/'tool-home'),'LANG':'C.UTF-8','TZ':'UTC','N8N_USER_FOLDER':str(WORK/'tool-home/n8n-state'),'N8N_DIAGNOSTICS_ENABLED':'false','N8N_VERSION_NOTIFICATIONS_ENABLED':'false','N8N_TEMPLATES_ENABLED':'false','N8N_PERSONALIZATION_ENABLED':'false','N8N_COMMUNITY_PACKAGES_ENABLED':'false','N8N_SECURE_COOKIE':'false','N8N_LOG_LEVEL':'warn','N8N_RUNNERS_MODE':'internal','NODE_OPTIONS':'--max-old-space-size=1536','NO_PROXY':'127.0.0.1,localhost'}
    try:
        for scenario in args.scenarios:
            STATE.update(scenario=scenario,requests=[],deliveries=[])
            wf=copy.deepcopy(source);wf['name']='SYNTHETIC integration test: '+scenario;wf['id']=hashlib.sha256(('coffee-engine-'+scenario).encode()).hexdigest()[:16]
            for n in wf['nodes']:
                par=n['parameters']
                if n['name']=='Configuration':
                    par['jsCode']=par['jsCode'].replace("'octocat/Hello-World'","'fixture/repo'").replace("const until = new Date();","const until = new Date('2026-09-17T00:00:00Z');").replace('REPLACE/REPLACE','123456789/synthetic-test-only')
                    if scenario=='normal-fr':par['jsCode']=par['jsCode'].replace("const language = 'EN'","const language = 'FR'")
                if n['name'].startswith('GitHub '):
                    par['authentication']='none';par.pop('genericAuthType',None);par['url']=par['url'].replace('https://api.github.com',base)
                if n['name']=='Claude Summary':par['authentication']='none';par.pop('genericAuthType',None);par['url']=base+'/messages'
                if n['name']=='Deliver Discord':par['url']=base+'/discord'
            wfpath=OUT/(scenario+'.workflow.json');wfpath.write_text(json.dumps(wf,indent=2))
            env['N8N_RUNNERS_BROKER_PORT']=str(free_port());env['N8N_PORT']=str(free_port())
            cli=[str(NODE_BINARY),str(N8N_CLI)]
            imp=subprocess.run(cli+['import:workflow','--input',str(wfpath)],env=env,cwd=ROOT,capture_output=True,text=True,timeout=180)
            (OUT/(scenario+'.import.log')).write_text(imp.stdout+'\n'+imp.stderr)
            if imp.returncode: raise RuntimeError('Workflow import failed: '+imp.stderr[-3000:]+imp.stdout[-3000:])
            cmd=cli+['execute','--id',wf['id'],'--rawOutput']
            started=datetime.datetime.now(datetime.timezone.utc).isoformat()
            try:r=subprocess.run(cmd,env=env,cwd=ROOT,capture_output=True,text=True,timeout=240);rc=r.returncode;stdout=r.stdout;stderr=r.stderr
            except subprocess.TimeoutExpired as e:rc=124;stdout=str(e.stdout);stderr=str(e.stderr)
            (OUT/(scenario+'.stdout.log')).write_text(stdout);(OUT/(scenario+'.stderr.log')).write_text(stderr)
            record={'scenario':scenario,'started_at':started,'engine':'n8n 2.39.6','exit_code':rc,'external_services':'synthetic local HTTP fixtures; no live Claude or Discord','requests':STATE['requests'],'deliveries':STATE['deliveries'],'workflow_source_sha256':hashlib.sha256((ROOT/'workflow.json').read_bytes()).hexdigest()}
            expected=1 if scenario in ('normal-en','normal-fr','empty') else 0
            record['test_passed']=(rc==0 and len(STATE['deliveries'])==expected) if expected else (not STATE['deliveries'] and ('incomplete GitHub search' if scenario=='incomplete' else 'Claude response truncated') in (stdout+stderr))
            if expected and record['test_passed']:
                counts=json.loads(next(x['body']['messages'][0]['content'] for x in STATE['requests'] if x['path']=='/messages'))['counts'];record['collected_counts']=counts
                record['test_passed']=counts==({'commits':0,'closedIssues':0,'mergedPRs':0} if scenario=='empty' else {'commits':2,'closedIssues':1,'mergedPRs':1})
            (OUT/(scenario+'.result.json')).write_text(json.dumps(record,indent=2));results.append(record)
            print(scenario,'exit',rc,'requests',len(STATE['requests']),'deliveries',len(STATE['deliveries']),'PASS' if record['test_passed'] else 'FAIL',flush=True)
            if not record['test_passed']: print((stderr+'\n'+stdout)[-6000:],flush=True);break
    finally:server.shutdown();server.server_close()
    (OUT/'summary.json').write_text(json.dumps(results,indent=2))
    return 0 if results and all(r['test_passed'] for r in results) else 1
if __name__=='__main__':raise SystemExit(main())
