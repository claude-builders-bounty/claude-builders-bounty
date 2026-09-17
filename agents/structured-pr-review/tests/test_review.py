from pathlib import Path
import importlib.util
import json
import unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('review',ROOT/'review.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
SHA='a'*40
URL='https://github.com/example/project/pull/7'
PATCH='@@ -1,2 +1,3 @@\n one\n+two\n three'
def metadata(sha=SHA,files=1):return {'head':{'sha':sha},'base':{'sha':'b'*40},'changed_files':files,'title':'Change'}
def file(i=0):return {'filename':f'file{i}.py','patch':PATCH,'additions':1,'deletions':0,'status':'modified'}
def packet():return {'url':URL,'repository':'example/project','number':7,'head_sha':SHA,'files':[{'path':'file0.py','patch':PATCH}],'limitations':[]}
def review():return {'summary':'A line is added. Existing surrounding lines remain.','risks':[],'suggestions':[],'confidence':'Medium'}
class Tests(unittest.TestCase):
 def test_url_valid(self):self.assertEqual(m.parse_pr(URL),('example/project',7))
 def test_url_rejects_shell_suffix(self):
  with self.assertRaises(m.ReviewError):m.parse_pr(URL+';touch /tmp/x')
 def test_url_rejects_wrong_host(self):
  with self.assertRaises(m.ReviewError):m.parse_pr(URL.replace('github.com','github.com.evil.invalid'))
 def test_url_rejects_userinfo(self):
  with self.assertRaises(m.ReviewError):m.parse_pr(URL.replace('github.com','github.com@evil.invalid'))
 def test_url_rejects_queries(self):
  with self.assertRaises(m.ReviewError):m.parse_pr(URL+'?token=x')
 def test_url_rejects_http(self):
  with self.assertRaises(m.ReviewError):m.parse_pr(URL.replace('https:','http:'))
 def test_collect_pinned(self):
  with patch.object(m,'api',side_effect=[metadata(),[file()],metadata()]):p=m.collect(URL,5000)
  self.assertEqual(p['head_sha'],SHA);self.assertFalse(p['tests_executed'])
 def test_collect_pagination(self):
  with patch.object(m,'api',side_effect=[metadata(files=101),[file(i) for i in range(100)],[file(100)],metadata(files=101)]) as api:p=m.collect(URL,100000)
  self.assertEqual(len(p['files']),101);self.assertIn('page=2',api.call_args_list[2].args[0])
 def test_changed_head_aborts(self):
  with patch.object(m,'api',side_effect=[metadata(),[file()],metadata('c'*40)]):
   with self.assertRaisesRegex(m.ReviewError,'changed'):m.collect(URL,5000)
 def test_short_pagination_aborts(self):
  with patch.object(m,'api',side_effect=[metadata(files=2),[file()]]):
   with self.assertRaises(m.ReviewError):m.collect(URL,5000)
 def test_duplicate_file_aborts(self):
  with patch.object(m,'api',side_effect=[metadata(files=2),[file(),file()]]):
   with self.assertRaises(m.ReviewError):m.collect(URL,5000)
 def test_missing_patch_is_visible(self):
  f=file();f.pop('patch')
  with patch.object(m,'api',side_effect=[metadata(),[f],metadata()]):p=m.collect(URL,5000)
  self.assertEqual(len(p['limitations']),1)
 def test_excess_diff_aborts(self):
  with patch.object(m,'api',side_effect=[metadata(),[file()]]):
   with self.assertRaisesRegex(m.ReviewError,'exceeds'):m.collect(URL,2)
 def test_bad_metadata_aborts(self):
  with patch.object(m,'api',return_value={}):
   with self.assertRaises(m.ReviewError):m.collect(URL,5000)
 def test_decode_structured_output(self):
  d,meta=m.decode_response(json.dumps({'structured_output':review(),'is_error':False,'total_cost_usd':0.01}))
  self.assertEqual(d,review());self.assertEqual(meta['total_cost_usd'],0.01)
 def test_decode_text_result(self):
  d,_=m.decode_response(json.dumps({'result':json.dumps(review())}));self.assertEqual(d,review())
 def test_decode_one_json_fence(self):
  value='```json\n'+json.dumps(review())+'\n```'
  d,_=m.decode_response(json.dumps({'result':value}));self.assertEqual(d,review())
 def test_fence_with_unrelated_prose_rejected(self):
  value='Summary: \n```json\n'+json.dumps(review())+'\n```'
  with self.assertRaises(m.ReviewError):m.decode_response(json.dumps({'result':value}))
 def test_multiple_json_blocks_rejected(self):
  value='```json\n'+json.dumps(review())+'\n```\n```json\n{}\n```'
  with self.assertRaises(m.ReviewError):m.decode_response(json.dumps({'result':value}))
 def test_decode_provider_error(self):
  with self.assertRaises(m.ReviewError):m.decode_response(json.dumps({'is_error':True,'result':'failed'}))
 def test_decode_invalid_json(self):
  with self.assertRaises(m.ReviewError):m.decode_response('invalid')
 def test_validate_good(self):self.assertEqual(m.validate(review(),packet()),review())
 def test_unknown_path_rejected(self):
  r=review();r['risks']=[{'path':'invented.py','line':1,'severity':'high','description':'x'}]
  with self.assertRaises(m.ReviewError):m.validate(r,packet())
 def test_invalid_line_rejected(self):
  r=review();r['risks']=[{'path':'file0.py','line':999,'severity':'high','description':'x'}]
  with self.assertRaises(m.ReviewError):m.validate(r,packet())
 def test_actual_hunk_line_accepted(self):
  r=review();r['risks']=[{'path':'file0.py','line':2,'severity':'medium','description':'x'}]
  self.assertEqual(m.validate(r,packet()),r)
 def test_incomplete_cannot_high_confidence(self):
  r=review();r['confidence']='High';p=packet();p['limitations']=['binary omitted']
  with self.assertRaises(m.ReviewError):m.validate(r,p)
 def test_extra_schema_key_rejected(self):
  r=review();r['approved']=True
  with self.assertRaises(m.ReviewError):m.validate(r,packet())
 def test_markdown_required_sections(self):
  s=m.render(review(),packet())
  for heading in ['## Summary','## Identified risks','## Improvement suggestions','## Confidence']:self.assertIn(heading,s)
  self.assertIn('no repository code',s.lower())
 def test_markdown_escapes_injected_html(self):
  r=review();r['summary']='<script>payload</script> A review.'
  self.assertNotIn('<script>',m.render(r,packet()))
 def extraction(self):
  return {'summary':[{'id':'s1','text':'A line is added.','evidence':[{'ref':'f0h1R2','quote':'two'}]}],'findings':[]}
 def audit(self):return {'decisions':[{'id':'s1','checks':[{'field':'text','actual':'The added line is present.','matches':True}]}]}
 def test_tools_disabled_and_model_input_data(self):
  outputs=[json.dumps({'structured_output':self.extraction()}),json.dumps({'structured_output':self.audit()})]
  with patch.object(m,'command',side_effect=outputs) as run:r,meta=m.infer(packet(),'sonnet',10,1.0)
  args=run.call_args.args[0];self.assertEqual(args[args.index('--tools')+1],'');self.assertIn('--strict-mcp-config',args);self.assertNotIn('push',args);self.assertIn('UNTRUSTED_DATA',run.call_args.kwargs['stdin'])
 def test_independent_verification_pass_receives_draft_and_source(self):
  outputs=[json.dumps({'structured_output':self.extraction()}),json.dumps({'structured_output':self.audit()})]
  with patch.object(m,'command',side_effect=outputs) as run:r,meta=m.infer(packet(),'sonnet',10,1.0)
  self.assertEqual(run.call_count,2);self.assertEqual(meta['passes'],2)
  self.assertIn('draft_review',run.call_args_list[1].kwargs['stdin']);self.assertIn('source_packet',run.call_args_list[1].kwargs['stdin'])
 def test_collect_only_no_model(self):
  with patch.object(m,'collect',return_value=packet()),patch.object(m,'infer') as infer,patch('builtins.print'):code=m.main(['--pr',URL,'--collect-only'])
  self.assertEqual(code,0);infer.assert_not_called()
 def test_negative_limits_fail(self):
  with patch.object(m,'collect') as collect,patch('builtins.print'):code=m.main(['--pr',URL,'--timeout','-1'])
  self.assertEqual(code,2);collect.assert_not_called()
 def test_missing_summary_rejected(self):
  r=review();r['summary']=' '
  with self.assertRaises(m.ReviewError):m.validate(r,packet())
 def test_provider_json_error_preserves_actual_reason(self):
  from types import SimpleNamespace
  result=SimpleNamespace(returncode=1,stdout=json.dumps({'duration_ms':0,'result':'OAuth session expired and could not be refreshed','is_error':True}),stderr='')
  with patch.object(m.subprocess,'run',return_value=result):
   with self.assertRaisesRegex(m.ReviewError,'OAuth session expired') as ctx:m.command(['claude','-p'])
  self.assertEqual(ctx.exception.diagnostics['stdout'],result.stdout)
 def test_evidence_records_failure_not_success(self):
  import tempfile
  with tempfile.TemporaryDirectory() as td:
   folder=Path(td)/'failed-evidence'
   with patch.object(m,'collect',return_value=packet()),patch.object(m,'infer',side_effect=m.ReviewError('test failure')),patch('builtins.print'):
    code=m.main(['--pr',URL,'--evidence-dir',str(folder)])
   self.assertEqual(code,2);self.assertTrue((folder/'input.json').exists());self.assertFalse((folder/'review.json').exists());self.assertFalse(json.loads((folder/'error.json').read_text())['success'])
 def test_cli_defaults_to_validated_native_profile(self):
  import io
  with patch.object(m,'collect',return_value=packet()),patch.object(m,'infer',return_value=(review(),{})) as inference,patch.object(m.sys,'stdout',io.StringIO()):code=m.main(['--pr',URL])
  self.assertEqual(code,0);self.assertEqual(inference.call_args.args[1],'opus');self.assertEqual(inference.call_args.args[4],'claude')
if __name__=='__main__':unittest.main()
