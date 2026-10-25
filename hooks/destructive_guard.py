#!/usr/bin/env python3
"""Claude Code PreToolUse guard. Inspects command text; never executes it."""

import json
import os
from pathlib import Path
import re
import shlex
import sys
from datetime import datetime, timezone


SQL_CLIENTS = {"psql", "mysql", "mariadb", "sqlite3", "duckdb", "sqlcmd"}
SHELLS = {"sh", "bash", "dash", "zsh", "ksh"}


def shell_unquoted(text):
    """Return positions outside quotes/comments, preserving shell text offsets."""
    positions, quote, i = set(), None, 0
    while i < len(text):
        ch = text[i]
        if ch == "\\" and quote != "'":
            i += 2
            continue
        if quote:
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
        elif ch == "#" and (i == 0 or text[i - 1].isspace() or text[i - 1] in ";&|()"):
            end = text.find("\n", i)
            i = len(text) if end == -1 else end
            continue
        else:
            positions.add(i)
        i += 1
    return positions


def without_comments(text):
    positions = shell_unquoted(text)
    # Comment markers are omitted from positions; quoted markers are retained.
    quote, i, output = None, 0, []
    while i < len(text):
        ch = text[i]
        if ch == "\\" and quote != "'":
            output.append(text[i:i + 2])
            i += 2
            continue
        if quote:
            if ch == quote:
                quote = None
        elif ch in "'\"":
            quote = ch
        elif ch == "#" and i not in positions:
            end = text.find("\n", i)
            i = len(text) if end == -1 else end
            continue
        output.append(ch)
        i += 1
    return "".join(output)


def sql_reason(text):
    """Find destructive SQL, ignoring comments, literals and quoted identifiers."""
    tokens = []
    # A dollar-quoted string must use the same delimiter at both ends.
    pattern = re.compile(
        r"--[^\n]*|/\*[\s\S]*?\*/|(?P<dollar>\$(?:[A-Za-z_]\w*)?\$)[\s\S]*?(?P=dollar)|"
        r"'(?:''|\\.|[^'])*'|\"(?:\"\"|[^\"])*\"|`(?:``|[^`])*`|\[[^\]]*\]|"
        r"[A-Za-z_][A-Za-z_0-9]*|[();]"
    )
    for match in pattern.finditer(text):
        token = match.group()
        if token.startswith(("--", "/*")):
            continue
        tokens.append(token.upper() if token[0].isalpha() else token)
    statements = [[]]
    for token in tokens:
        if token == ";":
            statements.append([])
        else:
            statements[-1].append(token)
    for statement in statements:
        for i, token in enumerate(statement):
            if token == "DROP" and statement[i + 1:i + 2] == ["TABLE"]:
                return "DROP TABLE removes a table and its data."
            if token == "TRUNCATE":
                return "TRUNCATE removes all rows from a table."
            if token == "DELETE" and statement[i + 1:i + 2] == ["FROM"]:
                depth = 0
                for following in statement[i + 2:]:
                    if following == "(":
                        depth += 1
                    elif following == ")":
                        depth -= 1
                    elif following == "WHERE" and depth == 0:
                        break
                else:
                    return "DELETE FROM without a WHERE clause removes all rows."
    return None


def substitutions(text):
    """Yield literal command substitutions outside single-quoted shell text."""
    i, quote = 0, None
    while i < len(text):
        if text[i] == "\\":
            i += 2
            continue
        if quote == "'":
            if text[i] == "'":
                quote = None
            i += 1
            continue
        if text[i] in "'\"":
            if quote == text[i]:
                quote = None
            elif quote is None:
                quote = text[i]
                i += 1
                continue
        if text.startswith("$(", i) and not text.startswith("$((", i):
            start, depth, j = i + 2, 1, i + 2
            inner_quote = None
            while j < len(text) and depth:
                ch = text[j]
                if ch == "\\":
                    j += 2
                    continue
                if inner_quote:
                    if ch == inner_quote:
                        inner_quote = None
                elif ch in "'\"":
                    inner_quote = ch
                elif ch == "(":
                    depth += 1
                elif ch == ")":
                    depth -= 1
                j += 1
            if depth == 0:
                yield text[start:j - 1]
                i = j
                continue
        elif text[i] == "`":
            end = i + 1
            while end < len(text):
                if text[end] == "\\":
                    end += 2
                    continue
                if text[end] == "`":
                    yield text[i + 1:end]
                    i = end
                    break
                end += 1
        i += 1


def unwrap(words):
    """Remove common execution prefixes while preserving the actual command."""
    words = list(words)
    while words:
        first = Path(words[0]).name
        if re.fullmatch(r"[A-Za-z_]\w*=.*", words[0], re.S):
            words.pop(0)
        elif first in {"if", "then", "elif", "else", "do", "while", "until", "!", "exec", "nohup"}:
            words.pop(0)
        elif first in {"sudo", "env", "command"}:
            words.pop(0)
            while words and words[0].startswith("-"):
                option = words.pop(0)
                if option == "--":
                    break
                if option in {"-u", "-g", "-h", "-p", "-C", "-T", "--user", "--group", "--chdir", "--unset"} and words:
                    words.pop(0)
        else:
            break
    return words


def command_reason(words, depth):
    words = unwrap(words)
    if not words:
        return None
    executable, args = Path(words[0]).name, words[1:]
    if executable == "rm":
        recursive = force = False
        for arg in args:
            if arg == "--":
                break
            if arg.startswith("--"):
                recursive |= arg == "--recursive"
                force |= arg == "--force"
            elif arg.startswith("-"):
                recursive |= bool(set(arg[1:]) & {"r", "R"})
                force |= "f" in arg[1:]
        if recursive and force:
            return "rm with recursive and force flags can delete a directory tree without confirmation."
    if executable == "git":
        i = 0
        while i < len(args) and args[i].startswith("-"):
            option = args[i]
            i += 1
            if option in {"-C", "-c", "--git-dir", "--work-tree", "--namespace", "--config-env"}:
                i += 1
        if i < len(args) and args[i] == "push":
            for arg in args[i + 1:]:
                if arg in {"--force", "--force-with-lease", "--force-if-includes"} or arg.startswith("--force-with-lease=") or (arg.startswith("-") and not arg.startswith("--") and "f" in arg[1:]) or arg.startswith("+"):
                    return "A forced git push can overwrite remote history."
    if executable in SHELLS:
        for i, arg in enumerate(args[:-1]):
            if arg.startswith("-") and not arg.startswith("--") and "c" in arg[1:]:
                return blocked_reason(args[i + 1], depth + 1)
    if executable == "eval":
        return blocked_reason(" ".join(args), depth + 1)
    if executable in SQL_CLIENTS or executable.upper() in {"DROP", "DELETE", "TRUNCATE"}:
        return sql_reason(" ".join(words))
    return None


def separate_heredocs(command):
    """Keep here-document data out of shell-command parsing."""
    lines = iter(command.splitlines(keepends=True))
    shell, documents = [], []
    for line in lines:
        shell.append(line)
        unquoted = shell_unquoted(line)
        for match in re.finditer(r"<<(?P<tabs>-)?\s*(['\"]?)([A-Za-z_]\w*)\2", line):
            if match.start() not in unquoted:
                continue
            body = []
            for content in lines:
                compare = content.lstrip("\t") if match['tabs'] else content
                if compare.rstrip("\r\n") == match[3]:
                    break
                body.append(content)
            documents.append((line, "".join(body), bool(match[2])))
    return "".join(shell), documents


def blocked_reason(command, depth=0):
    if depth > 20:
        return "Command nesting exceeds the guard's inspection limit."
    command, documents = separate_heredocs(command)
    command = without_comments(command)
    expanded_text = command + "".join(body for _, body, quoted in documents if not quoted)
    for nested in substitutions(expanded_text):
        reason = blocked_reason(nested, depth + 1)
        if reason:
            return reason
    # Preserve newlines as command separators, including multiline SQL input.
    lexer = shlex.shlex(command.replace("\\\n", ""), posix=True, punctuation_chars=";&|()\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""  # Bash only starts comments at a word boundary.
    segments, segment = [], []
    try:
        for token in lexer:
            if token and all(ch in ";&|()\n" for ch in token):
                if segment:
                    segments.append(segment)
                    segment = []
            else:
                segment.append(token)
        if segment:
            segments.append(segment)
    except ValueError:
        return "The shell command has unclosed quotes and cannot be inspected."
    for words in segments:
        reason = command_reason(words, depth)
        if reason:
            return reason
    # SQL arriving through a pipe or heredoc is still visible in this tool call.
    if any(unwrap(words) and Path(unwrap(words)[0]).name in SQL_CLIENTS for words in segments):
        for words in segments:
            clean = unwrap(words)
            if clean and clean[0] in {"echo", "printf"}:
                reason = sql_reason(" ".join(clean[1:]))
                if reason:
                    return reason
        for header, body, _ in documents:
            if any(re.search(r"\b" + client + r"\b", header) for client in SQL_CLIENTS):
                reason = sql_reason(body)
                if reason:
                    return reason
    return None


def deny(reason):
    print(json.dumps({"hookSpecificOutput": {
        "hookEventName": "PreToolUse", "permissionDecision": "deny",
        "permissionDecisionReason": "Blocked: " + reason,
    }}))


def main():
    try:
        event = json.load(sys.stdin)
        if not isinstance(event, dict):
            raise ValueError("expected an object")
        if event.get("tool_name") != "Bash" or event.get("hook_event_name", "PreToolUse") != "PreToolUse":
            return
        command = event["tool_input"]["command"]
        if not isinstance(command, str):
            raise ValueError("command must be text")
    except (ValueError, KeyError, TypeError):
        deny("Invalid hook input; expected a Bash command in tool_input.command.")
        return
    reason = blocked_reason(command)
    if not reason:
        return  # Leave the normal Claude Code permission flow unchanged.
    record = {"timestamp": datetime.now(timezone.utc).isoformat(), "command": command,
              "project_path": event.get("cwd", os.getcwd()), "reason": reason}
    try:
        log = Path.home() / ".claude" / "hooks" / "blocked.log"
        log.parent.mkdir(parents=True, exist_ok=True)
        # One append write keeps concurrent JSONL records separate; mode only
        # applies on creation, preserving an existing user's permissions.
        fd = os.open(log, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, ensure_ascii=True) + "\n")
    except OSError as error:
        reason += f" The attempt could not be written to blocked.log: {error}."
    deny(reason)


if __name__ == "__main__":
    main()
