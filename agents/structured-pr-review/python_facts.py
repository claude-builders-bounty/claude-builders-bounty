"""Syntactic facts from complete Python functions visible in a diff. Never executes code."""
import ast,re,textwrap

def facts(source):
    result=[]
    for hunk in source['hunks']:
        if not hunk['path'].endswith('.py'):continue
        for side,omit in [('before','added'),('after','removed')]:
            records=[r for r in hunk['lines'] if r['change']!=omit]
            for start,record in enumerate(records):
                match=re.match(r'^(\s*)(?:async\s+)?def\s+(\w+)\s*\(',record['text'])
                if not match:continue
                indent=len(match[1]);end=start+1
                while end<len(records):
                    text=records[end]['text']
                    if text.strip() and len(text)-len(text.lstrip())<=indent:break
                    end+=1
                snippet=textwrap.dedent('\n'.join(r['text'] for r in records[start:end]))
                try:tree=ast.parse(snippet)
                except (SyntaxError,IndentationError):continue
                if not tree.body or not isinstance(tree.body[0],(ast.FunctionDef,ast.AsyncFunctionDef)):continue
                function=tree.body[0];returns=[]
                def visit(node):
                    if node is not function and isinstance(node,(ast.FunctionDef,ast.AsyncFunctionDef,ast.Lambda)):return
                    if isinstance(node,ast.Return):
                        value=node.value
                        kind='tuple' if isinstance(value,ast.Tuple) else 'list' if isinstance(value,ast.List) else 'dict' if isinstance(value,ast.Dict) else 'none' if value is None or isinstance(value,ast.Constant) and value.value is None else 'string' if isinstance(value,ast.Constant) and isinstance(value.value,str) else 'other_expression'
                        returns.append({'expression':ast.unparse(value) if value is not None else 'None','syntax_kind':kind})
                    for child in ast.iter_child_nodes(node):visit(child)
                visit(function)
                result.append({'path':hunk['path'],'side':side,'function':function.name,'header_ref':record['ref'],'explicit_return_expressions':returns,'scope':'AST syntax only; no inferred execution or whole-program return-type guarantee'})
    return result


def return_claim_conflict(item, source):
    """Reject a quoted whole-function return claim that is only a tuple member.

    This deliberately narrow check is syntactic, not a general truth classifier.
    Descriptions of a named tuple component are not treated as whole returns.
    """
    text=item.get('text',item.get('description',''))
    for match in re.finditer(r"\breturns?\s+`([^`]+)`",text,flags=re.I):
        prefix=text[max(0,match.start()-70):match.start()].lower()
        if re.search(r'(?:element|member|component|field)\b[^.;]{0,25}$',prefix):continue
        try:claim=ast.dump(ast.parse(match.group(1),mode='eval').body,include_attributes=False)
        except SyntaxError:continue
        for fact in facts(source):
            if fact['side']!='after' or fact['function'] not in text:continue
            for result in fact['explicit_return_expressions']:
                if result['syntax_kind']!='tuple':continue
                expression=ast.parse(result['expression'],mode='eval').body
                if any(ast.dump(member,include_attributes=False)==claim for member in expression.elts):
                    return ('The quoted whole-function return claim matches only a tuple member; '
                            'the complete source return expression is '+result['expression'])
    return None
