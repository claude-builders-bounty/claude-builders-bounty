"""Explicit local HTTP fixtures for a real n8n manual run; no provider inference."""
import datetime as dt
import json
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

HERE = Path(__file__).parent
OUTPUT = Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / 'evidence'
OUTPUT.mkdir(parents=True, exist_ok=True)
PORT = 5681
requests = []
deliveries = []

workflow = json.loads((HERE / 'weekly-dev-summary.json').read_text())
workflow['name'] = 'Weekly dev summary — LOCAL FIXTURE TRANSPORTS'
workflow['id'] = 'Cbb5FixtureWorkflow'
workflow['active'] = False
workflow['settings']['saveManualExecutions'] = True
for node in workflow['nodes']:
    if node['name'] == 'Friday 17:00':
        node['disabled'] = True
    if node['name'] == 'Config':
        for assignment in node['parameters']['assignments']['assignments']:
            if assignment['name'] == 'githubRepo':
                assignment['value'] = 'fixture/example'
            if assignment['name'] == 'slackWebhookUrl':
                assignment['value'] = f'http://127.0.0.1:{PORT}/slack'
    if node['name'] == 'Fetch GitHub Weekly Activity':
        node['parameters']['url'] = f'http://127.0.0.1:{PORT}/graphql'
        for header in node['parameters']['headerParameters']['parameters']:
            if header['name'] == 'Authorization':
                header['value'] = 'Bearer FIXTURE_ONLY_NOT_A_CREDENTIAL'
    if node['name'] == 'Claude Weekly Narrative':
        node['parameters']['url'] = f'http://127.0.0.1:{PORT}/v1/messages'
        for header in node['parameters']['headerParameters']['parameters']:
            if header['name'] == 'x-api-key':
                header['value'] = 'FIXTURE_ONLY_NOT_A_CREDENTIAL'
    if node['name'] == 'Setup':
        node['parameters']['content'] = '## LOCAL FIXTURE TRANSPORTS\nReal n8n execution, synthetic GitHub activity, synthetic Claude response, loopback webhook only. No live inference or third-party delivery. Scheduler disabled.'
(OUTPUT / 'verification-workflow.json').write_text(json.dumps(workflow, indent=2, ensure_ascii=False) + '\n')

class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def do_POST(self):
        body = json.loads(self.rfile.read(int(self.headers.get('Content-Length', 0))))
        try:
            if self.path == '/graphql':
                v = body['variables']
                requests.append({'path': self.path, 'variables': v})
                assert 'until: $until' in body['query']
                timestamp = (dt.datetime.fromisoformat(v['until'].replace('Z', '+00:00')) - dt.timedelta(days=1)).isoformat()
                data = {'repository': {'defaultBranchRef': {'target': {}}}}
                for kind, count, cursor_name, skip_name, connection in [
                    ('commit', 135, 'commitCursor', 'skipCommits', 'history'),
                    ('issue', 205, 'issueCursor', 'skipIssues', 'closedIssues'),
                    ('pr', 1, 'prCursor', 'skipPrs', 'mergedPullRequests'),
                ]:
                    if v[skip_name]:
                        continue
                    start = int(v[cursor_name] or 0)
                    stop = min(start + 100, count)
                    records = []
                    for i in range(start, stop):
                        record = {'url': f'https://example.test/{kind}/{i}', 'author': {'login': 'fixture-user'}}
                        if kind == 'commit':
                            record.update(oid=f'{i:040x}', messageHeadline=f'Fixture commit {i}', committedDate=timestamp)
                        else:
                            record.update(number=i + 1, title=f'Fixture {kind} {i}')
                            record['closedAt' if kind == 'issue' else 'mergedAt'] = timestamp
                        records.append(record)
                    result = {'nodes': records, 'pageInfo': {'endCursor': str(stop), 'hasNextPage': stop < count}}
                    if kind == 'commit':
                        data['repository']['defaultBranchRef']['target']['history'] = result
                    else:
                        result['issueCount'] = count
                        data[connection] = result
                response = {'data': data}
            elif self.path == '/v1/messages':
                requests.append({'path': self.path, 'model': body['model'], 'prompt': body['messages'][0]['content']})
                prompt = body['messages'][0]['content']
                for text in ['Commits (135):', 'Closed issues (205):', 'Merged pull requests (1):']:
                    assert text in prompt, text
                assert '\n- 00000000:' in prompt
                assert '\\n-' not in prompt
                response = {'model': body['model'], 'stop_reason': 'end_turn', 'content': [
                    {'type': 'text', 'text': 'LOCAL FIXTURE RESPONSE — no live Claude inference.\n'},
                    {'type': 'text', 'text': '135 commits, 205 closed issues, and 1 merged PR verified across three GraphQL pages.'},
                ]}
            elif self.path == '/slack':
                assert body['text'].startswith('*Weekly dev summary — fixture/example*\n')
                assert 'LOCAL FIXTURE RESPONSE' in body['text']
                deliveries.append(body)
                response = {'ok': True, 'fixture_only': True, 'deliveries': len(deliveries)}
            else:
                raise ValueError('Unexpected endpoint')
            self.send_response(200)
        except Exception as exc:
            response = {'error': str(exc), 'fixture_only': True}
            self.send_response(400)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
        (OUTPUT / 'transport-receipt.json').write_text(json.dumps({'fixture_only': True, 'requests': requests, 'deliveries': deliveries}, indent=2) + '\n')

print(f'Loopback-only fixture receiver: http://127.0.0.1:{PORT}', flush=True)
HTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
