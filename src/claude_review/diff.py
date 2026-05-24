"""Small unified diff parser for review heuristics."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath


@dataclass(frozen=True)
class FileChange:
    path: str
    old_path: str
    additions: int
    deletions: int
    is_binary: bool
    is_deleted: bool
    is_renamed: bool

    @property
    def extension(self) -> str:
        suffix = PurePosixPath(self.path).suffix.lower()
        return suffix or "(none)"


def parse_unified_diff(diff: str) -> list[FileChange]:
    files: list[FileChange] = []
    current_path = ""
    old_path = ""
    additions = 0
    deletions = 0
    is_binary = False
    is_deleted = False
    is_renamed = False

    def flush() -> None:
        nonlocal current_path, old_path, additions, deletions, is_binary, is_deleted, is_renamed
        if current_path or old_path:
            files.append(
                FileChange(
                    path=current_path or old_path,
                    old_path=old_path,
                    additions=additions,
                    deletions=deletions,
                    is_binary=is_binary,
                    is_deleted=is_deleted,
                    is_renamed=is_renamed,
                )
            )
        current_path = ""
        old_path = ""
        additions = 0
        deletions = 0
        is_binary = False
        is_deleted = False
        is_renamed = False

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            flush()
            parts = line.split()
            if len(parts) >= 4:
                old_path = _strip_prefix(parts[2])
                current_path = _strip_prefix(parts[3])
            continue

        if line.startswith("rename from "):
            old_path = line.removeprefix("rename from ").strip()
            is_renamed = True
        elif line.startswith("rename to "):
            current_path = line.removeprefix("rename to ").strip()
            is_renamed = True
        elif line.startswith("deleted file mode"):
            is_deleted = True
        elif line.startswith("Binary files ") or line.startswith("GIT binary patch"):
            is_binary = True
        elif line.startswith("+++") or line.startswith("---"):
            continue
        elif line.startswith("+"):
            additions += 1
        elif line.startswith("-"):
            deletions += 1

    flush()
    return files


def _strip_prefix(path: str) -> str:
    if path.startswith("a/") or path.startswith("b/"):
        return path[2:]
    return path
