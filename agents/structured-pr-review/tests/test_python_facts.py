import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from python_facts import facts,return_claim_conflict

def source(lines,path='sample.py'):
    return {'hunks':[{'path':path,'lines':[{'ref':f'f0h1R{i+1}','text':line,'change':'added'} for i,line in enumerate(lines)]}]}
class PythonFacts(unittest.TestCase):
    def test_tuple_remains_tuple_when_member_empty(self):
        f=facts(source(['def row():','    return "NAME", ""']))
        after=next(x for x in f if x['side']=='after')
        self.assertEqual(after['explicit_return_expressions'][0]['syntax_kind'],'tuple')
    def test_scalar_is_not_tuple(self):
        f=facts(source(['def row():','    return ""']))
        self.assertEqual(f[0]['explicit_return_expressions'][0]['syntax_kind'],'string')
    def test_expression_does_not_invent_return_type(self):
        f=facts(source(['def row():','    return another_function()']))
        self.assertEqual(f[0]['explicit_return_expressions'][0]['syntax_kind'],'other_expression')
    def test_incomplete_definition_is_skipped(self):
        self.assertEqual(facts(source(['def row(','    value,'])),[])
    def test_nested_return_not_assigned_to_parent(self):
        f=facts(source(['def outer():','    def inner():','        return "inside"','    return (1, 2)']))
        outer=next(x for x in f if x['function']=='outer')
        self.assertEqual(len(outer['explicit_return_expressions']),1)
        self.assertEqual(outer['explicit_return_expressions'][0]['syntax_kind'],'tuple')
    def test_never_executes_source(self):
        f=facts(source(['def no_execution():','    raise RuntimeError("do not execute")','    return dangerous_call()']))
        self.assertEqual(f[0]['explicit_return_expressions'][0]['syntax_kind'],'other_expression')
    def test_non_python_is_ignored(self):
        self.assertEqual(facts(source(['def row():','    return ""'],'sample.txt')),[])
    def test_old_new_return_values_are_distinguished(self):
        s=source(['def row():','    return None','    return ("NAME", "")']);s['hunks'][0]['lines'][0]['change']='context';s['hunks'][0]['lines'][1]['change']='removed'
        f=facts(s);before=next(x for x in f if x['side']=='before');after=next(x for x in f if x['side']=='after')
        self.assertEqual(before['explicit_return_expressions'][0]['syntax_kind'],'none');self.assertEqual(after['explicit_return_expressions'][0]['syntax_kind'],'tuple')
    def test_complete_return_claim_cannot_use_tuple_member(self):
        s=source(['def get_record(help):','    return "NAME", help or ""'])
        item={'text':'get_record now returns `help or ""` instead of None.'}
        self.assertIsNotNone(return_claim_conflict(item,s))
    def test_correct_tuple_claim_is_retained(self):
        s=source(['def get_record(help):','    return "NAME", help or ""'])
        self.assertIsNone(return_claim_conflict({'text':'get_record returns `("NAME", help or "")`.'},s))
    def test_component_description_is_not_whole_return(self):
        s=source(['def get_record(help):','    return "NAME", help or ""'])
        self.assertIsNone(return_claim_conflict({'text':'get_record second component returns `help or ""`.'},s))
    def test_scalar_function_quote_is_valid(self):
        s=source(['def get_record(help):','    return help or ""'])
        self.assertIsNone(return_claim_conflict({'text':'get_record returns `help or ""`.'},s))
if __name__=='__main__':unittest.main()
