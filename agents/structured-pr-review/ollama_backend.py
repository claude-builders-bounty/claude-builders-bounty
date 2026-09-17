"""Optional direct-local inference backend. Does not emulate a cloud provider."""
from __future__ import annotations
import hashlib,json,re,time,urllib.request

def infer_json(stage,system,payload,schema,model,timeout):
    messages=[{'role':'system','content':system},{'role':'user','content':'REVIEW_STAGE: '+stage+'\nOUTPUT_SCHEMA: '+json.dumps(schema)+'\nUNTRUSTED_DATA: '+json.dumps(payload,ensure_ascii=False)}]
    body={'model':model,'messages':messages,'stream':False,'think':False,'format':schema,
          'keep_alive':'2m','options':{'num_ctx':8192 if model.startswith('gemma') else 16384,'num_predict':1400,'num_thread':2,'temperature':0,'seed':42}}
    started=time.monotonic()
    request=urllib.request.Request('http://127.0.0.1:11434/api/chat',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'},method='POST')
    with urllib.request.urlopen(request,timeout=timeout) as response:
        result=json.load(response)
    text=result['message']['content']
    metadata={'backend':'ollama-direct','model':model,'stage':stage,'duration_ms':round((time.monotonic()-started)*1000),
              'prompt_tokens':result.get('prompt_eval_count'),'output_tokens':result.get('eval_count'),
              'raw_output':text,'input_sha256':hashlib.sha256(json.dumps(messages,ensure_ascii=False).encode()).hexdigest(),
              'cloud_inference':False,'claude_code_used':False}
    if not result.get('done') or result.get('done_reason')=='length':raise ValueError('Incomplete local response')
    candidate=text.strip()
    fenced=re.fullmatch(r'```(?:json)?\s*\n([\s\S]*?)\n```',candidate,flags=re.I)
    if fenced:candidate=fenced.group(1)
    try:parsed=json.loads(candidate)
    except ValueError as exc:
        error=ValueError('Local response was not a single JSON object');error.raw_response=metadata
        raise error from exc
    return parsed,metadata
