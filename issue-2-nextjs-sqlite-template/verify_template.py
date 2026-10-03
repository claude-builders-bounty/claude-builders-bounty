from pathlib import Path
p=Path(__file__).with_name('CLAUDE.md').read_text()
required=['Stack and versions','Project structure','Database rules','Migrations','Commands','Component patterns','What we do not do (and why)','Rule rationale ledger','Change protocol for Claude Code']
missing=[x for x in required if x not in p]
assert not missing, missing
for phrase in ['server-only','prepared statements','Zod','better-sqlite3','Turso/libSQL','regression test']:
    assert phrase.lower() in p.lower(), phrase
print('template contract: PASS')

from json import loads
receipt=loads(Path(__file__).with_name('evidence').joinpath('comprehension-receipt.json').read_text())
assert receipt['exit_code']==0
assert receipt['asked_clarifying_questions'] is False
assert all(receipt['request']['context_markers_loaded'].values())
assert receipt['request']['user_agent'].startswith('claude-cli/2.1.288')
print('official Claude Code context receipt: PASS')
