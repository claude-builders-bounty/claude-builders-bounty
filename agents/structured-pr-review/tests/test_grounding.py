import copy,json,unittest,sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import grounding as g,review as m

def packet():
 return {'url':'https://github.com/example/project/pull/1','head_sha':'a'*40,'title':'Return a complete record','description':'Return the documented tuple, including empty help.','limitations':[],'files':[{'path':'api.py','patch':'@@ -1,3 +1,3 @@\n def record():\n-    return None\n+    return "name", ""\n # end'}]}
def good():
 return {'summary':[{'id':'s1','text':'The function now returns a tuple.','evidence':[{'ref':'f0h1R2','quote':'return "name", ""'}]}],'findings':[]}
def audit(verdict='supported'):
 return {'decisions':[{'id':'s1','checks':[{'field':'text','actual':verdict+': exact source expression comparison.','matches':verdict=='supported'}]}]}
class Grounding(unittest.TestCase):
 def test_old_and_new_line_numbers(self):
  idx=g.source_index(g.chunks(packet())[0]);self.assertEqual(idx['f0h1L2']['text'],'    return None');self.assertEqual(idx['f0h1R2']['text'],'    return "name", ""')
 def test_exact_full_tuple_quote_passes(self):self.assertEqual(len(g.candidates(good(),g.chunks(packet())[0])[0]),1)
 def test_scalar_fragment_cannot_quote_tuple(self):
  x=good();x['summary'][0]['evidence'][0]['quote']='""';valid,bad=g.candidates(x,g.chunks(packet())[0]);self.assertFalse(valid);self.assertEqual(len(bad),1)
 def test_invented_reference_excluded(self):
  x=good();x['summary'][0]['evidence'][0]['ref']='f8h1R2';self.assertFalse(g.candidates(x,g.chunks(packet())[0])[0])
 def test_unchanged_context_requires_causal_audit_not_blind_exclusion(self):
  x=good();x['summary'][0]['evidence']=[{'ref':'f0h1R1','quote':'def record():'}];items,bad=g.candidates(x,g.chunks(packet())[0]);self.assertEqual(len(items),1);self.assertTrue(items[0]['context_only'])
 def test_empty_quote_excluded(self):
  x=good();x['summary'][0]['evidence'][0]['quote']=' ';self.assertFalse(g.candidates(x,g.chunks(packet())[0])[0])
 def test_empty_evidence_excluded(self):
  x=good();x['summary'][0]['evidence']=[];self.assertFalse(g.candidates(x,g.chunks(packet())[0])[0])
 def test_duplicate_candidates_error(self):
  x=good();x['summary']*=2
  with self.assertRaisesRegex(ValueError,'duplicated'):g.candidates(x,g.chunks(packet())[0])
 def test_malformed_candidate_error(self):
  x=good();x['summary'][0]['extra']=1
  with self.assertRaises(ValueError):g.candidates(x,g.chunks(packet())[0])
 def test_extra_root_field_error(self):
  x=good();x['high_confidence']=True
  with self.assertRaises(ValueError):g.candidates(x,g.chunks(packet())[0])
 def test_audit_must_cover_all_candidates(self):
  with self.assertRaisesRegex(ValueError,'omitted'):g.audit_decisions({'decisions':[]},g.candidates(good(),g.chunks(packet())[0])[0])
 def test_audit_cannot_add_claim(self):
  x=audit();x['decisions'][0]['id']='invented'
  with self.assertRaises(ValueError):g.audit_decisions(x,g.candidates(good(),g.chunks(packet())[0])[0])
 def test_duplicate_verdict_error(self):
  x=audit();x['decisions']*=2
  with self.assertRaises(ValueError):g.audit_decisions(x,g.candidates(good(),g.chunks(packet())[0])[0])
 def test_model_cannot_invent_verdict(self):
  x=audit();x['decisions'][0]['checks'][0]['matches']='certain'
  with self.assertRaises(ValueError):g.audit_decisions(x,g.candidates(good(),g.chunks(packet())[0])[0])
 def test_all_negative_audit_verdicts_suppress_claim(self):
  for verdict in ['contradicted','intentional_change','insufficient_evidence']:
   with self.subTest(verdict=verdict),patch.object(m,'command',side_effect=[json.dumps({'structured_output':good()}),json.dumps({'structured_output':audit(verdict)})]):
    r,meta=m.infer(packet(),'sonnet',20,1);self.assertNotIn('returns a tuple',r['summary']);self.assertEqual(r['confidence'],'Low');self.assertEqual(len(meta['trace'][0]['excluded']),1)
 def test_matching_quote_alone_is_not_approval(self):
  x=good();x['summary'][0]['text']='The function returns an empty scalar.'
  with patch.object(m,'command',side_effect=[json.dumps({'structured_output':x}),json.dumps({'structured_output':audit('contradicted')})]):r,meta=m.infer(packet(),'sonnet',20,1)
  self.assertNotIn('empty scalar',r['summary']);self.assertEqual(meta['trace'][0]['draft'],x)
 def test_no_high_confidence_from_model_agreement(self):
  with patch.object(m,'command',side_effect=[json.dumps({'structured_output':good()}),json.dumps({'structured_output':audit()})]):r,meta=m.infer(packet(),'sonnet',20,1)
  self.assertEqual(r['confidence'],'Medium');self.assertEqual(meta['per_call_budget_usd'],0.5)
 def test_all_hunks_partitioned_exactly(self):
  p=packet();p['files']*=4;groups=g.chunks(p,700);refs=[x['ref'] for s in groups for h in s['hunks'] for x in h['lines']];self.assertEqual(len(refs),16);self.assertEqual(len(set(refs)),16);self.assertGreater(len(groups),1)
 def test_large_hunk_errors_not_truncates(self):
  with self.assertRaisesRegex(ValueError,'exceeds'):g.chunks(packet(),20)
 def test_nontext_patch_no_source_claim(self):
  p=packet();p['files'][0]['patch']=None;self.assertEqual(g.chunks(p),[])
 def test_proof_carrying_real_defect_not_always_empty(self):
  p=packet();p['files'][0]['patch']='@@ -1,2 +1,2 @@\n def ratio(total, count):\n-    return total / count if count else 0\n+    return total / count'
  finding={'id':'f1','description':'The zero-count guard was removed.','scenario':'count=0 now divides by zero.','suggestion':'Keep the zero-count guard.','severity':'high','evidence':[{'ref':'f0h1R2','quote':'return total / count'},{'ref':'f0h1L2','quote':'return total / count if count else 0'}]}
  draft={'summary':[],'findings':[finding]};check={'decisions':[{'id':'f1','checks':[{'field':field,'actual':'Zero divisor is no longer excluded.','matches':True} for field in ['description','scenario','suggestion','introduced_defect']]}]}
  with patch.object(m,'command',side_effect=[json.dumps({'structured_output':draft}),json.dumps({'structured_output':check})]):r,meta=m.infer(p,'sonnet',20,1)
  self.assertEqual(len(r['risks']),1);self.assertEqual(r['risks'][0]['line'],2);self.assertEqual(r['suggestions'],['Keep the zero-count guard.'])
 def test_oversized_hunk_fragments_keep_all_lines(self):
  p=packet();p['files'][0]['patch']='@@ -1,0 +1,100 @@\n'+'\n'.join('+value = '+str(i) for i in range(100))
  groups=g.chunks(p,1000);lines=[l for x in groups for h in x['hunks'] for l in h['lines']]
  self.assertEqual(len(lines),100);self.assertEqual(len({x['ref'] for x in lines}),100);self.assertTrue(any('fragment' in h for x in groups for h in x['hunks']))
 def test_compact_packet_keeps_exact_code(self):
  p=g.chunks(packet())[0];out=g.compact_source(p)
  for h in p['hunks']:
   for l in h['lines']:self.assertIn(l['ref']+' ['+l['change']+'] '+l['text'],out['hunks'][0]['lines'])
 def test_removed_guard_can_break_unchanged_division_line(self):
  p=packet();p['files'][0]['patch']='@@ -1,4 +1,2 @@\n def average(values):\n-    if not values:\n-        return 0\n     return sum(values) / len(values)'
  f={'id':'f1','description':'Empty input now divides by zero.','scenario':'average([]) raises ZeroDivisionError.','suggestion':'Restore the zero-count guard.','severity':'high','evidence':[{'ref':'f0h1R2','quote':'return sum(values) / len(values)'}]}
  d={'summary':[],'findings':[f]};a={'decisions':[{'id':'f1','checks':[{'field':field,'actual':'The removed guard prevented the empty-input failure.','matches':True} for field in ['description','scenario','suggestion','introduced_defect']]}]}
  with patch.object(m,'command',side_effect=[json.dumps({'structured_output':d}),json.dumps({'structured_output':a})]):out,meta=m.infer(p,'sonnet',10,1)
  self.assertEqual(len(out['risks']),1);self.assertEqual(out['risks'][0]['line'],2)
 def finding(self):
  return {'id':'f1','kind':'finding','description':'General bug','scenario':'Example','suggestion':'Fix'}
 def checks(self):
  return {'decisions':[{'id':'f1','checks':[{'field':f,'actual':'Source-derived behavior','matches':True} for f in ['description','scenario','suggestion','introduced_defect']]}]}
 def test_true_general_bug_does_not_excuse_false_scenario(self):
  a=self.checks();a['decisions'][0]['checks'][1]['matches']=False
  a['decisions'][0]['checks'][1]['actual']='First invalid index is 3, not the claimed 4.'
  self.assertEqual(g.audit_decisions(a,[self.finding()])['f1']['verdict'],'contradicted')
 def test_true_signature_does_not_excuse_wrong_return_value(self):
  a=self.checks();a['decisions'][0]['checks'][0]['matches']=False
  a['decisions'][0]['checks'][0]['actual']='The complete return value is a tuple, not a string.'
  self.assertEqual(g.audit_decisions(a,[self.finding()])['f1']['verdict'],'contradicted')
 def test_intended_behavior_is_not_accepted_as_bug(self):
  a=self.checks();a['decisions'][0]['checks'][3]['matches']=False
  self.assertEqual(g.audit_decisions(a,[self.finding()])['f1']['verdict'],'contradicted')
 def test_missing_suggestion_audit_is_rejected(self):
  a=self.checks();a['decisions'][0]['checks'].pop(2)
  with self.assertRaisesRegex(ValueError,'omitted'):g.audit_decisions(a,[self.finding()])
 def test_atomic_field_cannot_be_duplicated(self):
  a=self.checks();a['decisions'][0]['checks'][1]['field']='description'
  with self.assertRaisesRegex(ValueError,'duplicated'):g.audit_decisions(a,[self.finding()])
 def test_all_four_checks_are_needed(self):
  self.assertEqual(g.audit_decisions(self.checks(),[self.finding()])['f1']['verdict'],'supported')
if __name__=='__main__':unittest.main()
