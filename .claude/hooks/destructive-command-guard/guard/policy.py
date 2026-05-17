import re
import shlex
from dataclasses import dataclass


@dataclass(frozen=True)
class BlockDecision:
    rule_id: str
    reason: str


def find_block_reason(command: str) -> BlockDecision | None:
    """Return the first destructive pattern found in a Bash command."""
    normalized = command.strip()
    if not normalized:
        return None

    token_decision = _check_tokens(normalized)
    if token_decision:
        return token_decision

    sql_decision = _check_sql_patterns(normalized)
    if sql_decision:
        return sql_decision

    return None


def _check_tokens(command: str) -> BlockDecision | None:
    try:
        tokens = shlex.split(command, posix=True)
    except ValueError:
        tokens = command.split()

    if _has_recursive_force_rm(tokens):
        return BlockDecision(
            "rm_recursive_force",
            "Blocked rm with both recursive and force flags. Use a narrower delete command or ask the user first.",
        )

    if _has_force_git_push(tokens):
        return BlockDecision(
            "git_push_force",
            "Blocked git push with a force flag. Use a normal push, or ask the user before rewriting remote history.",
        )

    return None


def _has_recursive_force_rm(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if not _is_command_token(token, "rm"):
            continue

        recursive = False
        force = False
        for arg in tokens[index + 1 :]:
            if arg in {";", "&&", "||", "|"}:
                break
            if arg in {"--recursive", "--dir", "-r", "-R"}:
                recursive = True
            if arg in {"--force", "-f"}:
                force = True
            if arg.startswith("-") and not arg.startswith("--"):
                recursive = recursive or "r" in arg.lower()
                force = force or "f" in arg.lower()

        if recursive and force:
            return True

    return bool(re.search(r"(?<!\w)rm\s+-[A-Za-z]*r[A-Za-z]*f|(?<!\w)rm\s+-[A-Za-z]*f[A-Za-z]*r", command_join(tokens)))


def _has_force_git_push(tokens: list[str]) -> bool:
    for index, token in enumerate(tokens):
        if not _is_command_token(token, "git"):
            continue

        push_index = None
        for offset, arg in enumerate(tokens[index + 1 :], start=index + 1):
            if arg in {";", "&&", "||", "|"}:
                break
            if arg == "push":
                push_index = offset
                break

        if push_index is None:
            continue

        for arg in tokens[push_index + 1 :]:
            if arg in {";", "&&", "||", "|"}:
                break
            if arg in {"--force", "-f"} or arg.startswith("+"):
                return True

    return False


def _check_sql_patterns(command: str) -> BlockDecision | None:
    command_no_comments = _strip_sql_line_comments(command)

    if re.search(r"\bdrop\s+table\b", command_no_comments, re.IGNORECASE):
        return BlockDecision(
            "drop_table",
            "Blocked SQL DROP TABLE. This can permanently remove data; ask the user before running it.",
        )

    if re.search(r"\btruncate\s+(?:table\s+)?[A-Za-z_\"`]", command_no_comments, re.IGNORECASE):
        return BlockDecision(
            "truncate_table",
            "Blocked SQL TRUNCATE. This can erase a table quickly; ask the user before running it.",
        )

    if _has_delete_without_where(command_no_comments):
        return BlockDecision(
            "delete_without_where",
            "Blocked SQL DELETE FROM without a WHERE clause. Add a WHERE clause or ask the user before deleting rows.",
        )

    return None


def _has_delete_without_where(command: str) -> bool:
    for match in re.finditer(r"\bdelete\s+from\b", command, re.IGNORECASE):
        statement = command[match.start() :]
        statement = re.split(r";|\n|&&|\|\|", statement, maxsplit=1)[0]
        if not re.search(r"\bwhere\b", statement, re.IGNORECASE):
            return True

    return False


def _strip_sql_line_comments(command: str) -> str:
    return re.sub(r"--[^\n]*", "", command)


def _is_command_token(token: str, command_name: str) -> bool:
    return token == command_name or token.endswith(f"/{command_name}")


def command_join(tokens: list[str]) -> str:
    return " ".join(tokens)

