from pathlib import PurePosixPath
import re


def safe(value):
    """Render untrusted GitHub metadata as plain Markdown text."""
    value = re.sub(r'[\x00-\x1f\x7f]', ' ', str(value))
    value = value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return re.sub(r'([\\`*_{}\[\]()#!|])', r'\\\1', value)


def is_test(path):
    p = PurePosixPath(path)
    return any(x.lower() in {'test', 'tests', '__tests__'} for x in p.parts) or p.name.startswith('test_') or bool(re.search(r'\.(test|spec)\.', p.name))


class HeuristicEngine:
    """Backend slot: implement review(snapshot) -> Markdown for other engines."""
    def review(self, snapshot):
        files = snapshot['files']
        risks, suggestions = [], []
        added = deleted = tests_added = 0
        source_paths = []
        missing = []
        strong = False
        for f in files:
            path = f['filename']
            patch = f.get('patch') or ''
            if not patch:
                missing.append(path)
            plus = minus = 0
            in_hunk = False
            line_number = 0
            for line in patch.splitlines():
                if line.startswith('@@'):
                    h = re.match(r'@@ -\d+(?:,\d+)? \+(\d+)', line)
                    in_hunk = bool(h)
                    if h:
                        line_number = int(h.group(1))
                    continue
                if not in_hunk:
                    continue
                if line.startswith('+'):
                    plus += 1
                    if re.search(r'AKIA[0-9A-Z]{16}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|(?:api[_-]?key|password|secret|token)\s*[:=]\s*[\"\'][^\"\']{8,}[\"\']', line[1:], re.I):
                        risks.append(f'Potential credential pattern at {safe(path)}:{line_number}; value redacted, may be a placeholder.')
                        suggestions.append(f'Inspect {safe(path)}:{line_number}; remove and rotate any actual exposed credential.')
                        strong = True
                    line_number += 1
                elif line.startswith('-'):
                    minus += 1
                elif line.startswith(' '):
                    line_number += 1
                else:
                    in_hunk = False
            added += plus
            deleted += minus
            if is_test(path):
                tests_added += plus
            elif PurePosixPath(path).suffix in {'.py', '.js', '.ts', '.tsx', '.go', '.rs', '.java', '.rb', '.c', '.cpp'}:
                source_paths.append(path)
            lower = path.lower()
            signals = []
            if 'lock' in PurePosixPath(lower).name or PurePosixPath(lower).name in {'requirements.txt', 'pyproject.toml', 'package.json', '.pre-commit-config.yaml'}:
                signals.append(('Dependency/tooling configuration changed', 'Check compatibility and run dependency/tooling checks'))
            if any(x in lower.split('/') for x in ('migration', 'migrations')) or lower.endswith('.sql'):
                signals.append(('Database/schema path changed', 'Check rollback, data safety, and migration ordering'))
            if lower.startswith('.github/workflows/'):
                signals.append(('CI workflow changed', 'Inspect permissions and untrusted input handling'))
            if any(x in lower for x in ('auth', 'cookies', 'crypto', 'security')):
                signals.append(('Security/session-related path changed', 'Exercise boundary cases and existing security/session tests'))
            for risk, suggestion in signals:
                risks.append(f'{risk}: {safe(path)} (path signal, not a confirmed defect).')
                suggestions.append(f'{suggestion}: {safe(path)}.')
        total = added + deleted
        incomplete = len(files) != snapshot.get('changed_files', len(files)) or bool(missing) or added != snapshot.get('additions', added) or deleted != snapshot.get('deletions', deleted)
        if incomplete:
            risks.append('Patch coverage is incomplete or counts differ from metadata; binary, omitted, or truncated changes may be unreviewed.')
            suggestions.append('Inspect the full GitHub diff and any binary/omitted files before relying on this draft.')
        if total > 2000 or len(files) > 50:
            risks.append(f'Large diff: {len(files)} observed files and {total} observed changed lines increase review burden.')
            suggestions.append('Split review by subsystem and verify integration behavior.')
        if total and deleted / total > .6:
            risks.append(f'Deletion-heavy diff: {deleted / total:.0%} of observed changed lines are removals.')
            suggestions.append('Check removed behavior, callers, and compatibility.')
        if source_paths and not tests_added:
            risks.append('Source changes have no added test lines in the supplied patches; this does not establish missing coverage.')
            suggestions.append('Run existing tests and add regression cases for changed behavior where needed.')
        elif tests_added:
            suggestions.append(f'Run the changed tests ({tests_added} added test lines observed); test presence does not establish coverage or passing status.')
        if not total:
            risks.append('No textual changed lines available; behavioral conclusions cannot be drawn.')
            suggestions.append('Verify whether this is an empty, rename-only, or binary diff.')
        if not risks:
            risks.append('No configured risk signal detected in observed patches; correctness remains unverified.')
        if not suggestions:
            suggestions.append('Run repository checks and manually verify intended behavior before merging.')
        confidence = 'Low' if not total or incomplete or total > 2000 or len(files) > 50 else ('High' if strong else 'Med')
        names = ', '.join(safe(f['filename']) for f in files[:8]) or 'no files'
        if len(files) > 8:
            names += f', and {len(files)-8} more'
        summary = f'The supplied patches change {len(files)} files: {names}. Observed textual changes contain {added} additions and {deleted} deletions, including {tests_added} added test lines; this draft uses offline heuristics and does not execute the target code.'
        return '\n'.join([f'# PR review: {safe(snapshot.get("title", "Untitled"))}', '', f'PR: {snapshot["pr_url"]}', f'Head: {safe(snapshot.get("head_sha", "unknown"))}', f'Source: {safe(snapshot.get("source", "snapshot"))}', '', '## Summary of changes', '', summary, '', '## Identified risks', '', *['- '+r for r in risks], '', '## Improvement suggestions', '', *['- '+s for s in suggestions], '', '## Confidence', '', f'**{confidence}** (Medium abbreviated Med). Confidence concerns the observed heuristic signals, not merge safety; no target tests were run.', ''])
