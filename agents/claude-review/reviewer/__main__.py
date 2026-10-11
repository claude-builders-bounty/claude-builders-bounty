import argparse
import json
from pathlib import Path
import sys
from .github import MAX_BYTES, fetch_pr, parse_pr_url
from .engine import HeuristicEngine


def main(argv=None):
    parser = argparse.ArgumentParser(description='Read-only heuristic GitHub PR review draft')
    parser.add_argument('--pr', required=True)
    parser.add_argument('--out', type=Path)
    parser.add_argument('--snapshot', type=Path, help='Replay saved GitHub metadata and per-file patches without network')
    args = parser.parse_args(argv)
    try:
        identity = parse_pr_url(args.pr)
        if args.snapshot:
            with args.snapshot.open('rb') as handle:
                raw = handle.read(MAX_BYTES + 1)
            if len(raw) > MAX_BYTES:
                raise ValueError('Snapshot exceeds 8 MiB')
            data = json.loads(raw)
            if parse_pr_url(data['pr_url']) != identity:
                raise ValueError('Snapshot PR does not match --pr')
            if not isinstance(data['files'], list) or any(not isinstance(f.get('filename'), str) or not isinstance(f.get('patch', ''), (str, type(None))) for f in data['files']):
                raise ValueError('Invalid snapshot files')
        else:
            data = fetch_pr(args.pr)
        markdown = HeuristicEngine().review(data)
        if args.out:
            args.out.write_text(markdown, encoding='utf-8')
        sys.stdout.write(markdown)
        return 0
    except (ValueError, OSError, KeyError, TypeError, AttributeError) as exc:
        print(f'claude-review: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
