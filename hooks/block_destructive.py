#!/usr/bin/env python3
"""Inspect a Claude Bash tool call; never execute its command."""
import datetime as dt
import json
import os
from pathlib import Path
import re
import sys


def sql_reason(query):
    # Remove comments and quoted values/identifiers before looking for keywords.
    # Quoting must not hide a later statement or manufacture a WHERE clause.
    pattern = r"--[^\n]*|/\*[\s\S]*?\*/|'(?:''|\\.|[^'\\])*'|\"(?:\"\"|[^\"])*\"|`(?:``|[^`])*`|\[[^\]]*\]|\$(\w*)\$[\s\S]*?\$\1\$"
    clean = re.sub(pattern, lambda m: ' ' * len(m.group()), query)
    for statement in clean.split(';'):
        words = re.findall(r'[A-Za-z_]+|[()]', statement.upper())
        if words[:2] == ['DROP', 'TABLE']:
            return 'DROP TABLE removes a table'
        if words[:1] == ['TRUNCATE']:
            return 'TRUNCATE removes all rows'
        depth, top = 0, []
        for word in words:
            if word == '(':
                depth += 1
            elif word == ')':
                depth = max(0, depth - 1)
            elif depth == 0:
                top.append(word)
        # Also handle a CTE preceding DELETE, without trusting a WHERE in the CTE.
        for index in range(len(top) - 1):
            if top[index:index + 2] == ['DELETE', 'FROM']:
                if 'WHERE' not in top[index + 2:]:
                    return 'DELETE FROM without a WHERE clause removes all rows'
    return None


def substitutions(command):
    """Yield literal $(...) / backtick bodies, excluding single-quoted data."""
    i, quote = 0, None
    while i < len(command):
        char = command[i]
        if char == '\\' and quote != "'":
            i += 2
            continue
        if quote == "'":
            if char == "'":
                quote = None
        elif char == "'" and quote is None:
            quote = "'"
        elif char == '"':
            quote = None if quote == '"' else '"'
        elif char == '#' and quote is None and (i == 0 or command[i - 1].isspace()):
            end = command.find('\n', i)
            i = len(command) if end == -1 else end
            continue
        elif char == '`':
            end = i + 1
            while end < len(command):
                if command[end] == '\\':
                    end += 2
                elif command[end] == '`':
                    break
                else:
                    end += 1
            yield command[i + 1:end]
            i = end
        elif command.startswith('$(', i) and not command.startswith('$((', i):
            start, end, depth, inner_quote = i + 2, i + 2, 1, None
            while end < len(command) and depth:
                current = command[end]
                if current == '\\' and inner_quote != "'":
                    end += 2
                    continue
                if inner_quote:
                    if current == inner_quote:
                        inner_quote = None
                elif current in "'\"":
                    inner_quote = current
                elif current == '(':
                    depth += 1
                elif current == ')':
                    depth -= 1
                end += 1
            yield command[start:end - 1 if depth == 0 else end]
            i = end - 1
        i += 1


def command_words(words):
    # Handle the usual command wrappers without mistaking echo/grep data for code.
    while words and (re.match(r'^[A-Za-z_]\w*=', words[0]) or
                     words[0] in ('then', 'do', 'else', '!', '{')):
        words = words[1:]
    while words and Path(words[0]).name in ('sudo', 'env', 'command', 'exec'):
        wrapper, words = Path(words[0]).name, words[1:]
        while words and (words[0].startswith('-') or re.match(r'^[A-Za-z_]\w*=', words[0])):
            option, words = words[0], words[1:]
            if option in ('-u', '-g', '-C', '--user', '--group', '--chdir') and words:
                words = words[1:]
    return words


def segment_reason(words, depth):
    words = command_words(words)
    if not words:
        return None
    name, args = Path(words[0]).name, words[1:]
    if name == 'rm':
        recursive, force = False, False
        for arg in args:
            if arg == '--':
                break
            recursive |= arg == '--recursive' or (arg.startswith('-') and not arg.startswith('--') and bool(set(arg[1:]) & set('rR')))
            force |= arg == '--force' or (arg.startswith('-') and not arg.startswith('--') and 'f' in arg[1:])
        if recursive and force:
            return 'rm with recursive and force options deletes trees without prompting'
    if name == 'git':
        while args and args[0].startswith('-'):
            option, args = args[0], args[1:]
            if option in ('-C', '-c', '--git-dir', '--work-tree', '--namespace') and args:
                args = args[1:]
        if args[:1] == ['push']:
            for arg in args[1:]:
                if arg == '--':
                    break
                if (arg in ('-f', '--force') or arg.startswith('--force-with-lease') or
                        (arg.startswith('-') and not arg.startswith('--') and 'f' in arg[1:]) or arg.startswith('+')):
                    return 'forced git push can overwrite remote history'
    if name in ('sh', 'bash', 'dash', 'zsh', 'ksh'):
        for index, arg in enumerate(args):
            if arg.startswith('-') and not arg.startswith('--') and 'c' in arg[1:] and index + 1 < len(args):
                return blocked_reason(args[index + 1], depth + 1)
    if name in ('mysql', 'mariadb', 'psql'):
        short, long = ('-c', '--command') if name == 'psql' else ('-e', '--execute')
        for index, arg in enumerate(args):
            if arg in (short, long) and index + 1 < len(args):
                reason = sql_reason(args[index + 1])
                if reason:
                    return reason
            if arg.startswith(long + '='):
                reason = sql_reason(arg.partition('=')[2])
                if reason:
                    return reason
            if arg.startswith(short) and len(arg) > 2:
                reason = sql_reason(arg[2:])
                if reason:
                    return reason
    if name == 'sqlite3':
        for arg in args:
            reason = sql_reason(arg)
            if reason:
                return reason
    return None


def shell_segments(command, with_operators=False):
    """Split literal shell words; keep quoted separators as data, not operators."""
    words, word, quote, started, i = [], [], None, False, 0
    while i < len(command):
        char = command[i]
        if char == '\\' and quote != "'":
            if i + 1 == len(command):
                raise ValueError('incomplete escape')
            if command[i + 1] != '\n':
                word.append(command[i + 1])
                started = True
            i += 2
            continue
        if quote:
            if char == quote:
                quote = None
            else:
                word.append(char)
        elif char in "'\"":
            quote, started = char, True
        elif char == '#' and not started:
            end = command.find('\n', i)
            i = len(command) if end == -1 else end
            continue
        elif char in ' \t\r;&|()\n':
            if started:
                words.append(''.join(word))
                word, started = [], False
            if char in ';&|()\n':
                yield (words, char) if with_operators else words
                words = []
        else:
            word.append(char)
            started = True
        i += 1
    if quote:
        raise ValueError('incomplete quote')
    if started:
        words.append(''.join(word))
    yield (words, '') if with_operators else words


def active_heredoc_positions(line):
    """Find << operators outside quotes, escapes and trailing shell comments."""
    positions, quote, index = set(), None, 0
    while index < len(line):
        char = line[index]
        if char == '\\' and quote != "'":
            index += 2
            continue
        if quote:
            if char == quote:
                quote = None
        elif char in "'\"":
            quote = char
        elif char == '#' and (index == 0 or line[index - 1] in ' \t;&|()'):
            break
        elif line.startswith('<<', index):
            positions.add(index)
            index += 1
        index += 1
    return positions


def heredocs(command):
    """Separate common literal heredoc bodies from shell command lines."""
    lines, cleaned, bodies, index = command.splitlines(keepends=True), [], [], 0
    pattern = re.compile(r"<<(-?)\s*(?:'([^']+)'|\"([^\"]+)\"|([A-Za-z_]\w*))")
    while index < len(lines):
        line = lines[index]
        positions = active_heredoc_positions(line)
        matches = [m for m in pattern.finditer(line) if m.start() in positions]
        cleaned.append(line)
        index += 1
        for match in matches:
            marker = match[2] or match[3] or match[4]
            body = []
            while index < len(lines):
                current = lines[index].rstrip('\r\n')
                if match[1]:
                    current = current.lstrip('\t')
                index += 1
                if current == marker:
                    break
                body.append(current)
            else:
                raise ValueError('unterminated heredoc')
            bodies.append((line, '\n'.join(body), bool(match[2] or match[3])))
    return ''.join(cleaned), bodies


def blocked_reason(command, depth=0):
    if depth > 8:
        return 'nested shell command exceeds the inspection limit'
    # Plain SQL statements are covered as well as SQL client command arguments.
    if re.match(r'^\s*(?:DROP\s+TABLE|TRUNCATE\b|DELETE\s+FROM|WITH\b|SELECT\b)', command, re.I):
        reason = sql_reason(command)
        if reason:
            return reason
    try:
        command, documents = heredocs(command)
    except ValueError:
        return 'heredoc terminator is missing; cannot safely inspect this command'
    for header, body, quoted in documents:
        segments = list(shell_segments(header))
        if any(command_words(words) and Path(command_words(words)[0]).name in
               ('mysql', 'mariadb', 'psql', 'sqlite3') for words in segments):
            reason = sql_reason(body)
            if reason:
                return reason
        if not quoted:
            for nested in substitutions(body):
                reason = blocked_reason(nested, depth + 1)
                if reason:
                    return reason
    for body in substitutions(command):
        reason = blocked_reason(body, depth + 1)
        if reason:
            return reason
    try:
        segments = list(shell_segments(command, with_operators=True))
        for index, (segment, operator) in enumerate(segments):
            reason = segment_reason(segment, depth)
            if reason:
                return reason
            current = command_words(segment)
            if current and Path(current[0]).name in ('mysql', 'mariadb', 'psql', 'sqlite3') and index and segments[index - 1][1] == '|':
                previous = command_words(segments[index - 1][0])
                if previous and previous[0] in ('echo', 'printf'):
                    for query in previous[1:] + [' '.join(previous[1:])]:
                        reason = sql_reason(query)
                        if reason:
                            return reason
    except ValueError:
        return 'shell quoting is incomplete; cannot safely inspect this command'
    return None


def main():
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            raise ValueError('expected a JSON object')
        if event.get('hook_event_name', 'PreToolUse') != 'PreToolUse' or event.get('tool_name') != 'Bash':
            return 0
        command = event['tool_input']['command']
        if not isinstance(command, str):
            raise ValueError('expected a string command')
        reason = blocked_reason(command)
    except (ValueError, KeyError, TypeError, RecursionError) as error:
        print('Blocked: invalid Bash hook input or inspection failure: ' + str(error), file=sys.stderr)
        return 2
    if not reason:
        return 0  # No allow decision: retain Claude's normal permission checks.
    record = {'timestamp': dt.datetime.now(dt.timezone.utc).isoformat(),
              'command': command, 'project_path': event.get('cwd', ''), 'reason': reason}
    try:
        directory = Path.home() / '.claude' / 'hooks'
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        fd = os.open(directory / 'blocked.log', os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, 'a', encoding='utf-8') as log:
            log.write(json.dumps(record, ensure_ascii=True) + '\n')
    except OSError as error:
        print('Audit log could not be written: ' + str(error), file=sys.stderr)
    print('Blocked: ' + reason + '. Choose a non-destructive command; this hook does not execute commands.', file=sys.stderr)
    return 2


if __name__ == '__main__':
    raise SystemExit(main())
