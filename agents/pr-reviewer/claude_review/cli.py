#!/usr/bin/env python3
"""Structured PR reviewer for Claude Builders Bounty issue #4.

The tool is intentionally dependency-free. It can review a local diff file or
fetch a GitHub PR diff by URL, then produce deterministic Markdown with the
sections required by the bounty.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import textwrap
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


CONFIDENCE_VALUES = {"Low", "Medium", "High"}
SEVERITY_RANK = {"Low": 1, "Medium": 2, "High": 3}
MAX_DIFF_CHARS_DEFAULT = 500_000
MIN_DIFF_CHARS = 1_000
REVIEW_MARKER = "<!-- claude-review-agent -->"
CONFIG_FILENAMES = (".claude-review.yml", ".claude-review.yaml", ".claude-review.json")
MAX_REPO_SCAN_FILES = 2_000
MAX_REPO_SCAN_FILE_BYTES = 500_000
TEXT_EXTENSIONS = {
    ".c",
    ".cc",
    ".cpp",
    ".cs",
    ".go",
    ".java",
    ".js",
    ".jsx",
    ".kt",
    ".mjs",
    ".php",
    ".py",
    ".rb",
    ".rs",
    ".scala",
    ".swift",
    ".ts",
    ".tsx",
}
RUNTIME_RISK_EXTENSIONS = TEXT_EXTENSIONS | {
    ".bash",
    ".env",
    ".ini",
    ".json",
    ".ps1",
    ".psm1",
    ".sh",
    ".sql",
    ".toml",
    ".yaml",
    ".yml",
    ".zsh",
}
DOCUMENTATION_EXTENSIONS = {".adoc", ".diff", ".md", ".patch", ".rst", ".txt"}
NOISE_PATH_MARKERS = (
    "/docs/",
    "/examples/",
    "/fixtures/",
    "/samples/",
)
SCRIPT_FILENAMES = {".env", "dockerfile", "makefile"}
EXCLUDED_SCAN_DIRS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".next",
    ".pytest_cache",
    ".tox",
    ".venv",
    "__pycache__",
    "build",
    "coverage",
    "dist",
    "node_modules",
    "target",
    "vendor",
}


@dataclass(frozen=True)
class PullRequestRef:
    owner: str
    repo: str
    number: int
    url: str

    @property
    def slug(self) -> str:
        return f"{self.owner}/{self.repo}"


@dataclass
class PullRequestMetadata:
    url: str = ""
    title: str = "Local diff"
    author: str = "unknown"
    number: str = "n/a"
    additions: int | None = None
    deletions: int | None = None
    changed_files: int | None = None
    base_ref: str = ""
    head_ref: str = ""


@dataclass
class DiffLine:
    path: str
    line: int | None
    text: str


@dataclass(frozen=True)
class SymbolChange:
    name: str
    kind: str
    path: str
    line: int | None
    evidence: str

    @property
    def location(self) -> str:
        if self.line is not None:
            return f"{self.path}:{self.line}"
        return self.path


@dataclass
class Finding:
    code: str
    severity: str
    message: str
    suggestion: str
    path: str = ""
    line: int | None = None
    evidence: str = ""

    @property
    def location(self) -> str:
        if self.path and self.line is not None:
            return f"{self.path}:{self.line}"
        if self.path:
            return self.path
        return "global"


@dataclass
class ReviewConfig:
    disabled_rules: set[str] = field(default_factory=set)
    ignored_paths: list[str] = field(default_factory=list)
    severity_overrides: dict[str, str] = field(default_factory=dict)


@dataclass
class DiffStats:
    files: list[str] = field(default_factory=list)
    added_lines: list[str] = field(default_factory=list)
    added_records: list[DiffLine] = field(default_factory=list)
    removed_records: list[DiffLine] = field(default_factory=list)
    symbol_changes: list[SymbolChange] = field(default_factory=list)
    new_files: set[str] = field(default_factory=set)
    removed_lines: list[str] = field(default_factory=list)
    total_additions: int = 0
    total_deletions: int = 0
    truncated: bool = False

    @property
    def changed_files(self) -> int:
        return len(self.files)

    @property
    def tests_touched(self) -> bool:
        return any(is_test_path(path) for path in self.files)

    @property
    def primary_areas(self) -> list[str]:
        buckets: dict[str, int] = {}
        for path in self.files:
            bucket = path.split("/", 1)[0] if "/" in path else path
            if bucket:
                buckets[bucket] = buckets.get(bucket, 0) + 1
        return [name for name, _ in sorted(buckets.items(), key=lambda item: (-item[1], item[0]))[:4]]


@dataclass
class Review:
    summary: str
    risks: list[str]
    suggestions: list[str]
    confidence: str
    metadata: PullRequestMetadata
    stats: DiffStats
    findings: list[Finding] = field(default_factory=list)


class ReviewError(RuntimeError):
    """Raised when review input cannot be fetched or parsed."""


def parse_config_scalar(value: str) -> object:
    stripped = value.strip()
    if not stripped:
        return ""
    if stripped.startswith("[") and stripped.endswith("]"):
        inner = stripped[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("'\"") for item in inner.split(",") if item.strip()]
    if stripped.lower() in {"true", "false"}:
        return stripped.lower() == "true"
    return stripped.strip("'\"")


def parse_simple_yaml(text: str) -> dict[str, object]:
    result: dict[str, object] = {}
    current_key = ""
    for raw_line in text.splitlines():
        raw_line = raw_line.lstrip("\ufeff")
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if not raw_line.startswith((" ", "\t")):
            key, separator, value = raw_line.partition(":")
            if not separator:
                raise ReviewError(f"invalid config line: {raw_line}")
            current_key = key.strip()
            parsed = parse_config_scalar(value)
            result[current_key] = parsed if parsed != "" else []
            continue
        if not current_key:
            raise ReviewError(f"invalid indented config line: {raw_line}")
        stripped = raw_line.strip()
        if stripped.startswith("- "):
            existing = result.setdefault(current_key, [])
            if not isinstance(existing, list):
                raise ReviewError(f"config field {current_key!r} cannot mix list and map values")
            existing.append(str(parse_config_scalar(stripped[2:])))
            continue
        key, separator, value = stripped.partition(":")
        if not separator:
            raise ReviewError(f"invalid config line: {raw_line}")
        existing = result.get(current_key)
        if not isinstance(existing, dict):
            existing = {}
            result[current_key] = existing
        existing[key.strip()] = str(parse_config_scalar(value))
    return result


def coerce_string_list(value: object, field_name: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ReviewError(f"config field {field_name!r} must be a list")
    return [str(item).strip() for item in value if str(item).strip()]


def coerce_severity_overrides(value: object) -> dict[str, str]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ReviewError("config field 'severity_overrides' must be a map")
    result: dict[str, str] = {}
    for key, severity in value.items():
        normalized = str(severity).strip()
        if normalized not in CONFIDENCE_VALUES:
            raise ReviewError(
                f"config severity override for {key!r} must be Low, Medium, or High"
            )
        result[str(key).strip()] = normalized
    return result


def find_default_config(repo_root: str | Path | None = None) -> Path | None:
    roots: list[Path] = []
    if repo_root:
        roots.append(Path(repo_root))
    roots.append(Path.cwd())
    for root in roots:
        for name in CONFIG_FILENAMES:
            path = root / name
            if path.exists():
                return path
    return None


def load_review_config(config_path: str | None = None, repo_root: str | Path | None = None) -> ReviewConfig:
    path = Path(config_path) if config_path else find_default_config(repo_root)
    if path is None:
        return ReviewConfig()
    if not path.exists():
        raise ReviewError(f"config file does not exist: {path}")
    text = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix.lower() == ".json":
        try:
            raw = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ReviewError(f"invalid config JSON: {exc}") from exc
        if not isinstance(raw, dict):
            raise ReviewError("config JSON must be an object")
    else:
        raw = parse_simple_yaml(text)
    disabled_rules = set(coerce_string_list(raw.get("disabled_rules"), "disabled_rules"))
    ignored_paths = coerce_string_list(raw.get("ignored_paths"), "ignored_paths")
    severity_overrides = coerce_severity_overrides(raw.get("severity_overrides"))
    return ReviewConfig(
        disabled_rules=disabled_rules,
        ignored_paths=ignored_paths,
        severity_overrides=severity_overrides,
    )


def path_ignored(path: str, patterns: list[str]) -> bool:
    normalized = normalize_repo_relative_path(path)
    return any(fnmatch.fnmatch(normalized, pattern) for pattern in patterns)


def apply_review_config(findings: list[Finding], config: ReviewConfig | None) -> list[Finding]:
    if not config:
        return findings
    filtered: list[Finding] = []
    for finding in findings:
        if finding.code in config.disabled_rules:
            continue
        if finding.path and path_ignored(finding.path, config.ignored_paths):
            continue
        override = config.severity_overrides.get(finding.code)
        if override:
            finding = Finding(
                code=finding.code,
                severity=override,
                message=finding.message,
                suggestion=finding.suggestion,
                path=finding.path,
                line=finding.line,
                evidence=finding.evidence,
            )
        filtered.append(finding)
    return filtered


def parse_pr_url(value: str) -> PullRequestRef:
    text = value.strip()
    match = re.match(
        r"^https://github\.com/(?P<owner>[^/\s]+)/(?P<repo>[^/\s]+)/pull/(?P<number>\d+)(?:[/?#].*)?$",
        text,
    )
    if not match:
        match = re.match(
            r"^(?P<owner>[^/\s#]+)/(?P<repo>[^/\s#]+)#(?P<number>\d+)$",
            text,
        )
    if not match:
        raise ReviewError(
            "PR must look like https://github.com/owner/repo/pull/123 or owner/repo#123"
        )
    return PullRequestRef(
        owner=match.group("owner"),
        repo=match.group("repo"),
        number=int(match.group("number")),
        url=f"https://github.com/{match.group('owner')}/{match.group('repo')}/pull/{match.group('number')}",
    )


def run_command(args: list[str]) -> str:
    completed = subprocess.run(
        args,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
    )
    return completed.stdout


def fetch_with_gh(ref: PullRequestRef) -> tuple[PullRequestMetadata, str]:
    if not shutil.which("gh"):
        raise ReviewError("gh is not installed")

    view_raw = run_command(
        [
            "gh",
            "pr",
            "view",
            ref.url,
            "--json",
            "title,author,additions,deletions,changedFiles,url,number,baseRefName,headRefName",
        ]
    )
    view = json.loads(view_raw)
    author = view.get("author") or {}
    metadata = PullRequestMetadata(
        url=view.get("url") or ref.url,
        title=view.get("title") or f"PR #{ref.number}",
        author=author.get("login") or "unknown",
        number=str(view.get("number") or ref.number),
        additions=view.get("additions"),
        deletions=view.get("deletions"),
        changed_files=view.get("changedFiles"),
        base_ref=view.get("baseRefName") or "",
        head_ref=view.get("headRefName") or "",
    )
    diff = run_command(["gh", "pr", "diff", ref.url])
    return metadata, diff


def github_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "claude-review-agent",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def http_get(url: str, headers: dict[str, str]) -> bytes:
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return response.read()
    except urllib.error.HTTPError as exc:
        raise ReviewError(f"GitHub request failed with HTTP {exc.code}: {url}") from exc
    except urllib.error.URLError as exc:
        raise ReviewError(f"GitHub request failed: {exc.reason}") from exc


def fetch_with_api(ref: PullRequestRef) -> tuple[PullRequestMetadata, str]:
    api_url = f"https://api.github.com/repos/{ref.slug}/pulls/{ref.number}"
    raw = http_get(api_url, github_headers())
    payload = json.loads(raw.decode("utf-8"))
    user = payload.get("user") or {}
    head = payload.get("head") or {}
    base = payload.get("base") or {}
    metadata = PullRequestMetadata(
        url=payload.get("html_url") or ref.url,
        title=payload.get("title") or f"PR #{ref.number}",
        author=user.get("login") or "unknown",
        number=str(payload.get("number") or ref.number),
        additions=payload.get("additions"),
        deletions=payload.get("deletions"),
        changed_files=payload.get("changed_files"),
        base_ref=base.get("ref") or "",
        head_ref=head.get("ref") or "",
    )
    diff_headers = github_headers()
    diff_headers["Accept"] = "application/vnd.github.v3.diff"
    diff = http_get(api_url, diff_headers).decode("utf-8", errors="replace")
    return metadata, diff


def fetch_pr(ref: PullRequestRef, prefer_gh: bool = True) -> tuple[PullRequestMetadata, str]:
    errors: list[str] = []
    if prefer_gh:
        try:
            return fetch_with_gh(ref)
        except (ReviewError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
            errors.append(f"gh: {exc}")
    try:
        return fetch_with_api(ref)
    except ReviewError as exc:
        errors.append(f"api: {exc}")
    raise ReviewError("Unable to fetch PR diff. " + " | ".join(errors))


def trim_diff(diff: str, max_chars: int) -> tuple[str, bool]:
    if len(diff) <= max_chars:
        return diff, False
    head_len = max_chars // 2
    tail_len = max_chars - head_len
    marker = "\n\n[... diff truncated by claude-review ...]\n\n"
    return diff[:head_len] + marker + diff[-tail_len:], True


def parse_diff(diff: str, max_chars: int = MAX_DIFF_CHARS_DEFAULT) -> DiffStats:
    trimmed, truncated = trim_diff(diff, max_chars)
    stats = DiffStats(truncated=truncated)
    files: list[str] = []
    current_file = ""
    next_new_line: int | None = None
    current_symbol: SymbolChange | None = None
    old_file_was_dev_null = False
    for line in trimmed.splitlines():
        if line.startswith("diff --git "):
            paths = parse_diff_git_paths(line)
            if paths:
                old_path, new_path = paths
                path = normalize_diff_path(new_path)
                if path == "/dev/null":
                    path = normalize_diff_path(old_path)
                files.append(path)
                current_file = path
                next_new_line = None
                current_symbol = None
                old_file_was_dev_null = False
        elif line.startswith("new file mode ") and current_file:
            stats.new_files.add(current_file)
        elif line.startswith("--- /dev/null"):
            old_file_was_dev_null = True
        elif line.startswith("+++ b/"):
            path = normalize_diff_path(line[len("+++ ") :])
            if path != "/dev/null" and path not in files:
                files.append(path)
            if path != "/dev/null":
                current_file = path
                if old_file_was_dev_null:
                    stats.new_files.add(path)
        elif line.startswith("@@ "):
            next_new_line = parse_hunk_new_start(line)
            current_symbol = None
        elif line.startswith("+") and not line.startswith("+++"):
            stats.total_additions += 1
            text = line[1:]
            symbol = extract_symbol_change(text, current_file, next_new_line)
            if symbol:
                current_symbol = symbol
                add_symbol_change(stats, symbol)
            elif current_symbol and is_meaningful_code_line(text):
                add_symbol_change(stats, current_symbol)
            stats.added_lines.append(text)
            stats.added_records.append(DiffLine(current_file, next_new_line, text))
            if next_new_line is not None:
                next_new_line += 1
        elif line.startswith("-") and not line.startswith("---"):
            stats.total_deletions += 1
            text = line[1:]
            symbol = extract_symbol_change(text, current_file, None)
            if symbol:
                add_symbol_change(stats, symbol)
            elif current_symbol and is_meaningful_code_line(text):
                add_symbol_change(stats, current_symbol)
            stats.removed_lines.append(text)
            stats.removed_records.append(DiffLine(current_file, None, text))
        elif line.startswith(" ") and next_new_line is not None:
            text = line[1:]
            symbol = extract_symbol_change(text, current_file, next_new_line)
            if symbol:
                current_symbol = symbol
            next_new_line += 1

    stats.files = list(dict.fromkeys(files))
    return stats


def parse_hunk_new_start(line: str) -> int | None:
    match = re.search(r"\+(\d+)(?:,\d+)?", line)
    if not match:
        return None
    return int(match.group(1))


def parse_diff_git_paths(line: str) -> tuple[str, str] | None:
    """Parse a `diff --git` header while preserving paths that contain spaces."""
    prefix = "diff --git "
    if not line.startswith(prefix):
        return None
    remainder = line[len(prefix) :]
    if remainder.startswith('"'):
        tokens = re.findall(r'"((?:[^"\\]|\\.)*)"', remainder)
        if len(tokens) >= 2:
            return unquote_git_path(tokens[0]), unquote_git_path(tokens[1])
        return None
    marker = " b/"
    split_at = remainder.rfind(marker)
    if split_at == -1:
        return None
    return remainder[:split_at], remainder[split_at + 1 :]


def normalize_diff_path(path: str) -> str:
    path = unquote_git_path(path.strip())
    if path.startswith("a/") or path.startswith("b/"):
        return path[2:]
    return path


def unquote_git_path(path: str) -> str:
    if "\\" not in path:
        return path
    try:
        return bytes(path, "utf-8").decode("unicode_escape")
    except UnicodeDecodeError:
        return path


def is_test_path(path: str) -> bool:
    lowered = path.lower()
    return any(
        marker in lowered
        for marker in (
            "test/",
            "tests/",
            "__tests__",
            ".test.",
            ".spec.",
            "_test.",
            "fixtures/",
        )
    )


def path_suffix(path: str) -> str:
    normalized = normalize_repo_relative_path(path)
    return Path(normalized).suffix.lower()


def is_noise_path(path: str) -> bool:
    normalized = "/" + normalize_repo_relative_path(path).lower().lstrip("/")
    return any(marker in normalized for marker in NOISE_PATH_MARKERS) or path_suffix(normalized) in DOCUMENTATION_EXTENSIONS


def is_runtime_risk_path(path: str) -> bool:
    if not path or is_test_path(path) or is_noise_path(path):
        return False
    suffix = path_suffix(path)
    filename = normalize_repo_relative_path(path).rsplit("/", 1)[-1].lower()
    return suffix in RUNTIME_RISK_EXTENSIONS or filename in SCRIPT_FILENAMES or filename.startswith(".env.")


def is_symbol_reference_path(path: str) -> bool:
    if not path or is_noise_path(path):
        return False
    return path_suffix(path) in TEXT_EXTENSIONS


def strip_string_literals(text: str) -> str:
    return re.sub(
        r"""(?:[rRuUbBfF]{0,3})(?:"(?:\\.|[^"\\])*"|'(?:\\.|[^'\\])*')""",
        "",
        text,
    )


def is_meaningful_code_line(text: str) -> bool:
    stripped = text.strip().lstrip("\ufeff")
    if not stripped:
        return False
    return not stripped.startswith(("#", "//", "/*", "*", "\"\"\"", "'''"))


def add_symbol_change(stats: DiffStats, symbol: SymbolChange) -> None:
    if not is_trackable_symbol(symbol.name):
        return
    key = (symbol.name, symbol.kind, symbol.path, symbol.line)
    existing = {(item.name, item.kind, item.path, item.line) for item in stats.symbol_changes}
    if key not in existing:
        stats.symbol_changes.append(symbol)


def is_trackable_symbol(name: str) -> bool:
    if len(name) < 3:
        return False
    return name not in {
        "catch",
        "constructor",
        "else",
        "for",
        "get",
        "if",
        "main",
        "new",
        "obj",
        "old",
        "run",
        "set",
        "switch",
        "try",
        "while",
    }


def extract_symbol_change(text: str, path: str, line: int | None) -> SymbolChange | None:
    stripped = text.strip().lstrip("\ufeff")
    if not stripped or is_test_path(path) or not is_symbol_reference_path(path):
        return None

    patterns: list[tuple[str, str]] = [
        (r"^(?:async\s+)?def\s+([A-Za-z_]\w*)\s*\(", "python_function"),
        (r"^class\s+([A-Za-z_]\w*)\b", "class"),
        (r"^(?:export\s+)?(?:async\s+)?function\s+([A-Za-z_$][\w$]*)\s*\(", "js_function"),
        (r"^(?:export\s+)?class\s+([A-Za-z_$][\w$]*)\b", "class"),
        (
            r"^(?:export\s+)?(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*=>",
            "js_function",
        ),
        (r"^(?:public\s+|private\s+|protected\s+|static\s+|async\s+)*([A-Za-z_$][\w$]*)\s*\([^)]*\)\s*\{", "js_method"),
        (r"^([A-Za-z_$][\w$]*)\s*:\s*(?:async\s*)?(?:function\s*)?\([^)]*\)\s*(?:=>|\{)", "js_method"),
        (r"^export\s+(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=", "js_export"),
        (r"^module\.exports\.([A-Za-z_$][\w$]*)\s*=", "js_export"),
        (r"^exports\.([A-Za-z_$][\w$]*)\s*=", "js_export"),
        (r"^func\s+(?:\([^)]*\)\s*)?([A-Za-z_]\w*)\s*\(", "go_function"),
        (r"^(?:pub\s+)?fn\s+([A-Za-z_]\w*)\s*\(", "rust_function"),
        (r"^([A-Z][A-Z0-9_]{2,})\s*=", "constant"),
    ]
    for pattern, kind in patterns:
        match = re.search(pattern, stripped)
        if match:
            name = match.group(1)
            if is_trackable_symbol(name):
                return SymbolChange(
                    name=name,
                    kind=kind,
                    path=path,
                    line=line,
                    evidence=shorten_evidence(text),
                )
    return None


def symbol_reference_pattern(name: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![\w$]){re.escape(name)}(?![\w$])")


def references_symbol(text: str, symbol: SymbolChange) -> bool:
    if not is_trackable_symbol(symbol.name):
        return False
    return bool(symbol_reference_pattern(symbol.name).search(text))


def is_import_only_reference(text: str) -> bool:
    stripped = text.strip().lstrip("\ufeff")
    return bool(
        re.match(r"^(?:from\s+\S+\s+import|import\s+|export\s+\{)", stripped)
    )


def added_text(stats: DiffStats) -> str:
    return "\n".join(stats.added_lines)


def files_matching(stats: DiffStats, patterns: Iterable[str]) -> list[str]:
    regexes = [re.compile(pattern, re.IGNORECASE) for pattern in patterns]
    return [path for path in stats.files if any(regex.search(path) for regex in regexes)]


def first_matches(lines: Iterable[str], pattern: str, limit: int = 3) -> list[str]:
    regex = re.compile(pattern, re.IGNORECASE)
    matches: list[str] = []
    for line in lines:
        if regex.search(line):
            normalized = re.sub(r"\s+", " ", line).strip()
            if normalized:
                matches.append(normalized[:140])
        if len(matches) >= limit:
            break
    return matches


def first_record_matches(records: Iterable[DiffLine], pattern: str, limit: int = 3) -> list[DiffLine]:
    regex = re.compile(pattern, re.IGNORECASE)
    matches: list[DiffLine] = []
    for record in records:
        if regex.search(record.text):
            matches.append(record)
        if len(matches) >= limit:
            break
    return matches


def shorten_evidence(text: str, *, mask_string_literals: bool = False) -> str:
    normalized = re.sub(r"\s+", " ", text).strip()
    if mask_string_literals:
        normalized = re.sub(r"([:=]\s*['\"])[^'\"]{6,}(['\"])", r"\1...\2", normalized)
    return normalized[:140]


def delete_without_where(line: str) -> bool:
    stripped = re.sub(r"\s+", " ", line).strip().rstrip(";")
    return bool(re.search(r"\bdelete\s+from\b", stripped, re.IGNORECASE)) and not bool(
        re.search(r"\bwhere\b", stripped, re.IGNORECASE)
    )


def contains_force_delete(line: str) -> bool:
    pattern = r"\brm\s+-(?:[a-z]*r[a-z]*f|[a-z]*f[a-z]*r)\b"
    if re.search(pattern, strip_string_literals(line), re.IGNORECASE):
        return True
    if not re.search(pattern, line, re.IGNORECASE):
        return False
    return bool(
        re.search(
            r"\b(?:subprocess\.[A-Za-z_]+|os\.system|os\.popen|Popen|exec[lv]?[pe]?|shell\s*=)\b",
            line,
        )
    )


def format_dependency_refs(refs: list[DiffLine], limit: int = 3) -> str:
    locations = []
    for ref in refs[:limit]:
        location = f"{ref.path}:{ref.line}" if ref.line is not None else ref.path
        locations.append(location)
    suffix = "" if len(refs) <= limit else f" and {len(refs) - limit} more"
    return ", ".join(locations) + suffix


def dependency_diff_references(stats: DiffStats, symbol: SymbolChange) -> list[DiffLine]:
    refs: list[DiffLine] = []
    for record in stats.added_records:
        if record.path == symbol.path or is_test_path(record.path) or not is_symbol_reference_path(record.path):
            continue
        if references_symbol(record.text, symbol) and not is_import_only_reference(record.text):
            refs.append(record)
    return refs


def test_references_symbol(stats: DiffStats, symbol: SymbolChange) -> bool:
    for record in [*stats.added_records, *stats.removed_records]:
        if is_test_path(record.path) and references_symbol(record.text, symbol):
            return True
    return False


def should_scan_path(path: Path) -> bool:
    return path.suffix.lower() in TEXT_EXTENSIONS


def iter_repo_files(repo_root: Path) -> Iterable[Path]:
    scanned = 0
    for path in repo_root.rglob("*"):
        if scanned >= MAX_REPO_SCAN_FILES:
            break
        if not path.is_file():
            continue
        relative_parts = set(path.relative_to(repo_root).parts)
        if relative_parts & EXCLUDED_SCAN_DIRS:
            continue
        if not should_scan_path(path):
            continue
        try:
            if path.stat().st_size > MAX_REPO_SCAN_FILE_BYTES:
                continue
        except OSError:
            continue
        scanned += 1
        yield path


def repo_symbol_references(
    repo_root: str | Path | None,
    stats: DiffStats,
    symbol: SymbolChange,
    limit: int = 6,
) -> list[DiffLine]:
    if not repo_root:
        return []
    root = Path(repo_root)
    if not root.exists() or not root.is_dir():
        raise ReviewError(f"--repo-root must be an existing directory: {repo_root}")

    changed_files = {normalize_repo_relative_path(path) for path in stats.files}
    refs: list[DiffLine] = []
    pattern = symbol_reference_pattern(symbol.name)
    for path in iter_repo_files(root):
        relative = normalize_repo_relative_path(path.relative_to(root).as_posix())
        if (
            relative in changed_files
            or relative == normalize_repo_relative_path(symbol.path)
            or is_test_path(relative)
            or not is_symbol_reference_path(relative)
        ):
            continue
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        import_ref: DiffLine | None = None
        for line_number, line in enumerate(lines, start=1):
            if pattern.search(line):
                ref = DiffLine(relative, line_number, shorten_evidence(line))
                if is_import_only_reference(line):
                    import_ref = import_ref or ref
                    continue
                refs.append(ref)
                break
        else:
            if import_ref:
                refs.append(import_ref)
        if len(refs) >= limit:
            break
    return refs


def normalize_repo_relative_path(path: str) -> str:
    normalized = path.replace("\\", "/")
    while normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized.lstrip("/")


def build_dependency_findings(stats: DiffStats, repo_root: str | Path | None = None) -> list[Finding]:
    findings: list[Finding] = []
    seen: set[tuple[str, str]] = set()
    for symbol in stats.symbol_changes:
        diff_refs = dependency_diff_references(stats, symbol)
        if diff_refs:
            first = diff_refs[0]
            code = "DEPENDENT_USAGE_UNTESTED" if not stats.tests_touched else "DEPENDENT_USAGE_CHANGED"
            severity = "Medium" if not stats.tests_touched else "Low"
            findings.append(
                Finding(
                    code=code,
                    severity=severity,
                    message=(
                        f"Changed symbol `{symbol.name}` from {symbol.location} is used by "
                        f"{len(diff_refs)} non-test changed caller(s); dependent behavior may shift with this PR."
                    ),
                    suggestion=(
                        f"Add or verify integration coverage for `{symbol.name}` through the changed caller path(s): "
                        f"{format_dependency_refs(diff_refs)}."
                    ),
                    path=first.path,
                    line=first.line,
                    evidence=shorten_evidence(first.text),
                )
            )
            seen.add((symbol.name, "diff"))

        repo_refs = repo_symbol_references(repo_root, stats, symbol)
        if repo_refs:
            key = (symbol.name, "repo")
            if key in seen:
                continue
            first = repo_refs[0]
            findings.append(
                Finding(
                    code="DEPENDENT_USAGE_OUTSIDE_DIFF",
                    severity="Medium",
                    message=(
                        f"Changed symbol `{symbol.name}` from {symbol.location} is referenced by "
                        f"{len(repo_refs)} non-test file(s) outside the PR diff."
                    ),
                    suggestion=(
                        f"Review downstream caller behavior and run or add targeted tests for `{symbol.name}`; "
                        f"detected reference(s): {format_dependency_refs(repo_refs)}."
                    ),
                    path=first.path,
                    line=first.line,
                    evidence=f"{symbol.name} referenced by {format_dependency_refs(repo_refs)}",
                )
            )

        if (
            stats.tests_touched
            and normalize_repo_relative_path(symbol.path) not in stats.new_files
            and not test_references_symbol(stats, symbol)
        ):
            key = (symbol.name, "test_relevance")
            if key in seen:
                continue
            findings.append(
                Finding(
                    code="CHANGED_SYMBOL_WITHOUT_RELEVANT_TEST",
                    severity="Medium",
                    message=(
                        f"Tests changed, but no changed test line references changed symbol `{symbol.name}` from {symbol.location}; "
                        "coverage may be unrelated to the modified behavior."
                    ),
                    suggestion=(
                        f"Add or verify a test that exercises `{symbol.name}` directly or through a caller affected by this PR."
                    ),
                    path=symbol.path,
                    line=symbol.line,
                    evidence=symbol.evidence,
                )
            )
    return findings


def build_findings(stats: DiffStats, repo_root: str | Path | None = None) -> list[Finding]:
    findings: list[Finding] = []
    total_delta = stats.total_additions + stats.total_deletions
    runtime_records = [record for record in stats.added_records if is_runtime_risk_path(record.path)]

    def add_record_finding(
        code: str,
        severity: str,
        message: str,
        suggestion: str,
        record: DiffLine,
        *,
        mask_string_literals: bool = False,
    ) -> None:
        findings.append(
            Finding(
                code=code,
                severity=severity,
                message=message,
                suggestion=suggestion,
                path=record.path,
                line=record.line,
                evidence=shorten_evidence(record.text, mask_string_literals=mask_string_literals),
            )
        )

    secret_hits = first_record_matches(
        runtime_records,
        r"\b(api[_-]?key|secret|token|private[_-]?key|password)\b\s*[:=]\s*['\"][^'\"]{6,}",
        limit=2,
    )
    for record in secret_hits:
        add_record_finding(
            "SECRET_LITERAL",
            "High",
            "Possible credential-like literal was added; verify it is a placeholder or move it to environment configuration.",
            "Replace credential-like values with documented environment variables and add a safe example value.",
            record,
            mask_string_literals=True,
        )

    for record in [item for item in runtime_records if delete_without_where(item.text)][:2]:
        add_record_finding(
            "SQL_DELETE_WITHOUT_WHERE",
            "High",
            "SQL DELETE statement without an obvious WHERE clause was added; confirm it cannot erase full tables in production.",
            "Document the data-safety path: migration order, rollback expectations, and production safeguards.",
            record,
        )

    for record in [item for item in runtime_records if contains_force_delete(item.text)][:2]:
        add_record_finding(
            "FORCE_DELETE",
            "High",
            "Recursive force-delete shell command appears in added code; ensure it is scoped to disposable paths and covered by tests.",
            "Validate destructive filesystem operations against a fixed workspace root and avoid broad recursive deletes.",
            record,
        )

    shell_records = [
        record
        for record in runtime_records
        if re.search(r"\bshell\s*=\s*True\b", strip_string_literals(record.text), re.IGNORECASE)
    ][:2]
    for record in shell_records:
        add_record_finding(
            "SHELL_TRUE",
            "High",
            "A subprocess call enables shell=True, which can introduce command-injection risk if any input is user-controlled.",
            "Avoid shell interpretation where possible; pass arguments as a list and validate any user-controlled input.",
            record,
        )

    todo_records = [
        record
        for record in runtime_records
        if re.search(r"\bTODO\b|\bFIXME\b", strip_string_literals(record.text), re.IGNORECASE)
    ][:2]
    for record in todo_records:
        add_record_finding(
            "TODO_IN_CHANGE",
            "Medium",
            "New TODO/FIXME marker indicates incomplete follow-up work inside the submitted changes.",
            "Resolve the TODO/FIXME before submission or link it to a tracked follow-up with clear acceptance criteria.",
            record,
        )

    auth_files = files_matching(stats, [r"auth", r"session", r"jwt", r"oauth", r"permission", r"middleware"])
    if auth_files and not stats.tests_touched:
        findings.append(
            Finding(
                code="AUTH_WITHOUT_TESTS",
                severity="Medium",
                message=f"Security-sensitive files changed without accompanying tests: {', '.join(auth_files[:3])}.",
                suggestion="Add focused tests around authentication, authorization, session, or middleware behavior changed by this PR.",
                path=auth_files[0],
            )
        )

    migration_files = files_matching(stats, [r"migration", r"schema", r"database", r"\.sql$"])
    if migration_files:
        findings.append(
            Finding(
                code="DB_SCHEMA_CHANGE",
                severity="Medium",
                message="Database or schema files changed; review backward compatibility, rollback behavior, and data migration safety.",
                suggestion="Document the data-safety path: migration order, rollback expectations, and production safeguards.",
                path=migration_files[0],
            )
        )

    dependency_files = files_matching(
        stats,
        [
            r"package-lock\.json$",
            r"pnpm-lock\.yaml$",
            r"yarn\.lock$",
            r"requirements\.txt$",
            r"poetry\.lock$",
            r"Cargo\.lock$",
        ],
    )
    if dependency_files:
        findings.append(
            Finding(
                code="DEPENDENCY_CHANGE",
                severity="Medium",
                message="Dependency lockfile or manifest changed; review transitive dependency impact and supply-chain risk.",
                suggestion="Call out direct dependency changes and run the repository's normal dependency audit or lockfile validation.",
                path=dependency_files[0],
            )
        )

    if stats.changed_files >= 20 or total_delta >= 800:
        findings.append(
            Finding(
                code="LARGE_DIFF",
                severity="Medium",
                message="Large diff size may hide unrelated behavior changes; consider splitting or asking for targeted review by subsystem.",
                suggestion="Split unrelated concerns into smaller PRs or add a reviewer guide that maps files to behavior changes.",
            )
        )

    if stats.changed_files > 0 and not stats.tests_touched:
        findings.append(
            Finding(
                code="NO_TEST_CHANGES",
                severity="Medium",
                message="No test files were changed, so regression coverage for the modified behavior is unclear.",
                suggestion="Add or update focused tests that exercise the changed behavior and at least one failure path.",
            )
        )

    if stats.truncated:
        findings.append(
            Finding(
                code="DIFF_TRUNCATED",
                severity="High",
                message="The diff was truncated before analysis; review confidence is limited for omitted sections.",
                suggestion="Re-run with a higher --max-diff-chars value or review the omitted files manually before approval.",
            )
        )

    findings.extend(build_dependency_findings(stats, repo_root=repo_root))
    return findings


def finding_to_risk(finding: Finding) -> str:
    risk = f"[{finding.severity}][{finding.code}] {finding.location} - {finding.message}"
    if finding.evidence:
        risk += f" Evidence: `{finding.evidence}`."
    return risk


def build_risks(stats: DiffStats, findings: list[Finding]) -> list[str]:
    if findings:
        return [finding_to_risk(finding) for finding in findings]
    return [
        "No high-risk patterns were detected by static diff analysis; still verify behavior with project tests."
    ]


def build_suggestions(stats: DiffStats, findings: list[Finding]) -> list[str]:
    suggestions = [finding.suggestion for finding in findings if finding.suggestion.strip()]
    if not suggestions:
        if not stats.tests_touched:
            suggestions.append(
                "Add or update focused tests that exercise the changed behavior and at least one failure path."
            )
        else:
            suggestions.append(
                "Run the repository's normal test, lint, and type-check commands before merging."
            )

    suggestions.append(
        "Include reviewer-facing verification notes that list the exact commands run and their pass/fail status."
    )
    return list(dict.fromkeys(suggestions))


def choose_confidence(stats: DiffStats, findings: list[Finding]) -> str:
    total_delta = stats.total_additions + stats.total_deletions
    if stats.truncated or total_delta >= 1_200 or stats.changed_files >= 30:
        return "Low"
    if any(finding.severity == "High" for finding in findings):
        return "Medium"
    if any(finding.severity == "Medium" for finding in findings):
        return "Medium"
    if not stats.tests_touched or total_delta >= 400:
        return "Medium"
    return "High"


def summarize(metadata: PullRequestMetadata, stats: DiffStats) -> str:
    areas = ", ".join(stats.primary_areas) if stats.primary_areas else "the supplied diff"
    title = metadata.title.strip() or "the pull request"
    file_count = metadata.changed_files if metadata.changed_files is not None else stats.changed_files
    additions = metadata.additions if metadata.additions is not None else stats.total_additions
    deletions = metadata.deletions if metadata.deletions is not None else stats.total_deletions
    test_sentence = (
        "The diff includes test-related files, which improves review confidence."
        if stats.tests_touched
        else "The diff does not appear to include test changes, so behavior coverage should be confirmed separately."
    )
    return (
        f"This review covers {title} and examines {file_count} changed file(s) with about "
        f"{additions} additions and {deletions} deletions. The main touched area(s) are {areas}. "
        f"{test_sentence}"
    )


def review_prompt(metadata: PullRequestMetadata, diff: str, max_diff_chars: int) -> str:
    trimmed, truncated = trim_diff(diff, max_diff_chars)
    truncation_note = (
        "The diff was truncated symmetrically before being sent to you."
        if truncated
        else "The full supplied diff is included."
    )
    header = textwrap.dedent(
        f"""\
        You are reviewing a GitHub pull request for merge readiness.

        Return only a JSON object with these exact keys:
        - "summary": 2-3 sentences describing the change and test coverage.
        - "risks": an array of concrete risk strings. Include file paths and line numbers when available.
        - "suggestions": an array of actionable improvement strings.
        - "confidence": one of "Low", "Medium", or "High".

        Review metadata:
        - URL: {metadata.url or "local diff"}
        - Title: {metadata.title}
        - Author: {metadata.author}
        - Number: {metadata.number}
        - Base <- Head: {metadata.base_ref} <- {metadata.head_ref}
        - {truncation_note}
        """
    ).strip()
    return f"{header}\n\nDiff:\n```diff\n{trimmed}\n```\n"


def split_command(command: str) -> list[str]:
    try:
        parts = shlex.split(command, posix=True)
    except ValueError as exc:
        raise ReviewError(f"invalid --llm-command: {exc}") from exc
    if not parts:
        raise ReviewError("--llm-command cannot be empty")
    return parts


def run_llm_command(command: str, prompt: str) -> str:
    try:
        completed = subprocess.run(
            split_command(command),
            input=prompt,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            timeout=180,
        )
    except subprocess.TimeoutExpired as exc:
        raise ReviewError("--llm-command timed out") from exc
    except subprocess.CalledProcessError as exc:
        detail = (exc.stderr or exc.stdout or str(exc)).strip()
        raise ReviewError(f"--llm-command failed: {detail}") from exc
    return completed.stdout


def extract_json_object(raw: str) -> dict[str, object]:
    text = raw.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
    try:
        payload = json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise ReviewError("--llm-command did not return a JSON object")
        try:
            payload = json.loads(match.group(0))
        except json.JSONDecodeError as exc:
            raise ReviewError(f"--llm-command returned invalid JSON: {exc}") from exc
    if not isinstance(payload, dict):
        raise ReviewError("--llm-command must return a JSON object")
    return payload


def string_list(value: object, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise ReviewError(f"--llm-command JSON field {field_name!r} must be an array")
    result = [str(item).strip() for item in value if str(item).strip()]
    if not result:
        raise ReviewError(f"--llm-command JSON field {field_name!r} cannot be empty")
    return result


def merge_unique(primary: list[str], secondary: list[str]) -> list[str]:
    result: list[str] = []
    for item in [*primary, *secondary]:
        if item not in result:
            result.append(item)
    return result


def more_conservative_confidence(left: str, right: str) -> str:
    order = {"Low": 0, "Medium": 1, "High": 2}
    if left not in order:
        return right
    if right not in order:
        return left
    return left if order[left] <= order[right] else right


def build_llm_review(
    metadata: PullRequestMetadata,
    diff: str,
    max_diff_chars: int,
    command: str,
    repo_root: str | Path | None = None,
    config: ReviewConfig | None = None,
) -> Review:
    stats = parse_diff(diff, max_chars=max_diff_chars)
    findings = apply_review_config(build_findings(stats, repo_root=repo_root), config)
    payload = extract_json_object(run_llm_command(command, review_prompt(metadata, diff, max_diff_chars)))
    llm_risks = string_list(payload.get("risks"), "risks")
    llm_suggestions = string_list(payload.get("suggestions"), "suggestions")
    return Review(
        summary=str(payload.get("summary", "")).strip(),
        risks=merge_unique(llm_risks, build_risks(stats, findings) if findings else []),
        suggestions=merge_unique(
            llm_suggestions,
            build_suggestions(stats, findings) if findings else [],
        ),
        confidence=more_conservative_confidence(
            str(payload.get("confidence", "")).strip(),
            choose_confidence(stats, findings),
        ),
        metadata=metadata,
        stats=stats,
        findings=findings,
    )


def build_review(
    metadata: PullRequestMetadata,
    diff: str,
    max_diff_chars: int,
    repo_root: str | Path | None = None,
    config: ReviewConfig | None = None,
) -> Review:
    stats = parse_diff(diff, max_chars=max_diff_chars)
    findings = apply_review_config(build_findings(stats, repo_root=repo_root), config)
    risks = build_risks(stats, findings)
    suggestions = build_suggestions(stats, findings)
    confidence = choose_confidence(stats, findings)
    summary = summarize(metadata, stats)
    return Review(
        summary=summary,
        risks=risks,
        suggestions=suggestions,
        confidence=confidence,
        metadata=metadata,
        stats=stats,
        findings=findings,
    )


def markdown_list(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def workflow_command_escape(value: str, *, property_value: bool = False) -> str:
    escaped = value.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    if property_value:
        escaped = escaped.replace(":", "%3A").replace(",", "%2C")
    return escaped


def render_github_annotations(review: Review) -> str:
    lines: list[str] = []
    for finding in review.findings:
        if not finding.path:
            continue
        properties = [
            f"file={workflow_command_escape(finding.path, property_value=True)}",
            f"title={workflow_command_escape(f'{finding.severity} {finding.code}', property_value=True)}",
        ]
        if finding.line is not None:
            properties.append(f"line={finding.line}")
        message = workflow_command_escape(finding.message)
        lines.append(f"::warning {','.join(properties)}::{message}")
    return "\n".join(lines)


def append_step_summary(path: str | None, body: str) -> None:
    summary_path = path or os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        raise ReviewError("--step-summary requires a path or GITHUB_STEP_SUMMARY")
    with Path(summary_path).open("a", encoding="utf-8") as handle:
        handle.write(body.rstrip())
        handle.write("\n")


def render_markdown(review: Review) -> str:
    metadata_lines = [
        f"- PR: {review.metadata.url or 'local diff'}",
        f"- Author: {review.metadata.author}",
        f"- Changed files: {review.metadata.changed_files if review.metadata.changed_files is not None else review.stats.changed_files}",
    ]
    if review.metadata.base_ref or review.metadata.head_ref:
        metadata_lines.append(f"- Branches: {review.metadata.base_ref} <- {review.metadata.head_ref}")

    return (
        "## Claude Code PR Review\n\n"
        "### Review Metadata\n"
        f"{chr(10).join(metadata_lines)}\n\n"
        "### Summary\n"
        f"{review.summary}\n\n"
        "### Identified Risks\n"
        f"{markdown_list(review.risks)}\n\n"
        "### Improvement Suggestions\n"
        f"{markdown_list(review.suggestions)}\n\n"
        "### Confidence Score\n"
        f"{review.confidence}\n"
    )


def render_json(review: Review) -> str:
    payload = {
        "summary": review.summary,
        "risks": review.risks,
        "suggestions": review.suggestions,
        "confidence": review.confidence,
        "findings": [
            {
                "code": finding.code,
                "severity": finding.severity,
                "path": finding.path,
                "line": finding.line,
                "message": finding.message,
                "suggestion": finding.suggestion,
                "evidence": finding.evidence,
            }
            for finding in review.findings
        ],
        "metadata": {
            "url": review.metadata.url,
            "title": review.metadata.title,
            "author": review.metadata.author,
            "number": review.metadata.number,
            "changed_files": review.metadata.changed_files
            if review.metadata.changed_files is not None
            else review.stats.changed_files,
        },
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def sarif_level(severity: str) -> str:
    return {"High": "error", "Medium": "warning", "Low": "note"}.get(severity, "warning")


def render_sarif(review: Review) -> str:
    rules: dict[str, dict[str, object]] = {}
    results: list[dict[str, object]] = []
    for finding in review.findings:
        rules.setdefault(
            finding.code,
            {
                "id": finding.code,
                "name": finding.code,
                "shortDescription": {"text": finding.message},
                "help": {"text": finding.suggestion},
                "defaultConfiguration": {"level": sarif_level(finding.severity)},
            },
        )
        result: dict[str, object] = {
            "ruleId": finding.code,
            "level": sarif_level(finding.severity),
            "message": {"text": finding.message},
        }
        if finding.path:
            region: dict[str, int] = {}
            if finding.line is not None:
                region["startLine"] = finding.line
            result["locations"] = [
                {
                    "physicalLocation": {
                        "artifactLocation": {"uri": normalize_repo_relative_path(finding.path)},
                        **({"region": region} if region else {}),
                    }
                }
            ]
        if finding.evidence:
            result["properties"] = {"evidence": finding.evidence}
        results.append(result)

    payload = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "claude-review",
                        "informationUri": "https://github.com/claude-builders-bounty/claude-builders-bounty/issues/4",
                        "rules": list(rules.values()),
                    }
                },
                "results": results,
                "invocations": [
                    {
                        "executionSuccessful": True,
                        "properties": {
                            "confidence": review.confidence,
                            "summary": review.summary,
                        },
                    }
                ],
            }
        ],
    }
    return json.dumps(payload, indent=2, sort_keys=True)


def validate_review(review: Review) -> None:
    if not review.summary.strip():
        raise ReviewError("Generated review is missing a summary")
    sentence_count = len(re.findall(r"[.!?](?:\s|$)", review.summary))
    if sentence_count < 2 or sentence_count > 3:
        raise ReviewError("Generated summary must be 2-3 sentences")
    if not review.risks or any(not item.strip() for item in review.risks):
        raise ReviewError("Generated review must include nonempty risks")
    if not review.suggestions or any(not item.strip() for item in review.suggestions):
        raise ReviewError("Generated review must include nonempty suggestions")
    if review.confidence not in CONFIDENCE_VALUES:
        raise ReviewError("Generated confidence must be Low, Medium, or High")
    for finding in review.findings:
        if not finding.code.strip():
            raise ReviewError("Generated finding is missing a code")
        if finding.severity not in CONFIDENCE_VALUES:
            raise ReviewError("Generated finding severity must be Low, Medium, or High")
        if not finding.message.strip() or not finding.suggestion.strip():
            raise ReviewError("Generated finding must include message and suggestion")


def should_fail_review(review: Review, threshold: str | None) -> bool:
    if not threshold:
        return False
    threshold_rank = SEVERITY_RANK[threshold]
    return any(SEVERITY_RANK[finding.severity] >= threshold_rank for finding in review.findings)


def comment_body(body: str) -> str:
    if REVIEW_MARKER in body:
        return body
    return f"{body.rstrip()}\n\n{REVIEW_MARKER}\n"


def flatten_comment_pages(payload: object) -> list[dict[str, object]]:
    if isinstance(payload, list) and payload and all(isinstance(item, list) for item in payload):
        return [comment for page in payload for comment in page if isinstance(comment, dict)]
    if isinstance(payload, list):
        return [comment for comment in payload if isinstance(comment, dict)]
    return []


def find_existing_review_comment(pr_url: str) -> int | None:
    ref = parse_pr_url(pr_url)
    raw = run_command(
        [
            "gh",
            "api",
            f"repos/{ref.slug}/issues/{ref.number}/comments",
            "--paginate",
            "--slurp",
        ]
    )
    comments = flatten_comment_pages(json.loads(raw))
    for comment in reversed(comments):
        if REVIEW_MARKER in str(comment.get("body") or ""):
            comment_id = comment.get("id")
            if isinstance(comment_id, int):
                return comment_id
    return None


def update_comment(pr_url: str, body: str) -> bool:
    comment_id = find_existing_review_comment(pr_url)
    if comment_id is None:
        return False
    ref = parse_pr_url(pr_url)
    marked_body = comment_body(body)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".json") as tmp:
        json.dump({"body": marked_body}, tmp)
        tmp_path = tmp.name
    try:
        run_command(
            [
                "gh",
                "api",
                f"repos/{ref.slug}/issues/comments/{comment_id}",
                "--method",
                "PATCH",
                "--input",
                tmp_path,
            ]
        )
    finally:
        Path(tmp_path).unlink(missing_ok=True)
    return True


def post_comment(pr_url: str, body: str, update_existing: bool = False) -> None:
    if not shutil.which("gh"):
        raise ReviewError("--post-comment requires the GitHub CLI (gh)")
    marked_body = comment_body(body)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False, suffix=".md") as tmp:
        tmp.write(marked_body)
        tmp_path = tmp.name
    try:
        try:
            if update_existing and update_comment(pr_url, body):
                return
            run_command(["gh", "pr", "comment", pr_url, "--body-file", tmp_path])
        except subprocess.CalledProcessError as exc:
            detail = (exc.stderr or exc.stdout or str(exc)).strip()
            raise ReviewError(f"failed to post PR comment: {detail}") from exc
        except json.JSONDecodeError as exc:
            raise ReviewError(f"failed to parse existing PR comments: {exc}") from exc
    finally:
        Path(tmp_path).unlink(missing_ok=True)


def load_inputs(args: argparse.Namespace) -> tuple[PullRequestMetadata, str]:
    if args.diff_file:
        diff_path = Path(args.diff_file)
        if not diff_path.exists():
            raise ReviewError(f"Diff file does not exist: {diff_path}")
        return (
            PullRequestMetadata(url=str(diff_path), title=diff_path.name),
            diff_path.read_text(encoding="utf-8", errors="replace"),
        )
    if args.pr:
        return fetch_pr(parse_pr_url(args.pr), prefer_gh=not args.no_gh)
    raise ReviewError("Provide either --pr or --diff-file")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="claude-review",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Review a GitHub PR diff and emit structured Markdown.",
        epilog=textwrap.dedent(
            """\
            Examples:
              claude-review --pr https://github.com/owner/repo/pull/123
              claude-review --pr owner/repo#123
              claude-review --diff-file tests/fixtures/sample.diff --output review.md
              claude-review --pr https://github.com/owner/repo/pull/123 --post-comment
              claude-review --diff-file pr.diff --repo-root /path/to/checkout
              claude-review --pr https://github.com/owner/repo/pull/123 --llm-command "claude -p"
            """
        ),
    )
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument("--pr", help="GitHub pull request URL or owner/repo#123")
    input_group.add_argument("--diff-file", help="Path to a unified diff file")
    parser.add_argument("--output", "-o", help="Write review output to this file")
    parser.add_argument(
        "--format",
        choices=("markdown", "json", "sarif"),
        default="markdown",
        help="Output format (default: markdown)",
    )
    parser.add_argument(
        "--post-comment",
        action="store_true",
        help="Post the Markdown review as a PR comment with gh",
    )
    parser.add_argument(
        "--update-comment",
        action="store_true",
        help="Update the previous claude-review comment when one exists; implies --post-comment",
    )
    parser.add_argument(
        "--no-gh",
        action="store_true",
        help="Skip gh and use the GitHub REST API for --pr fetching",
    )
    parser.add_argument(
        "--max-diff-chars",
        type=int,
        default=MAX_DIFF_CHARS_DEFAULT,
        help=f"Maximum diff characters to analyze before symmetric truncation (default: {MAX_DIFF_CHARS_DEFAULT})",
    )
    parser.add_argument(
        "--prompt-only",
        action="store_true",
        help="Print the JSON-output review prompt for an external LLM and exit",
    )
    parser.add_argument(
        "--llm-command",
        help="Run this command with the review prompt on stdin and parse its JSON response",
    )
    parser.add_argument(
        "--repo-root",
        help="Optional local checkout root used to scan non-test downstream references to changed symbols",
    )
    parser.add_argument(
        "--config",
        help="Path to .claude-review.yml/.json; defaults to auto-detect in --repo-root or the current directory",
    )
    parser.add_argument(
        "--github-annotations",
        action="store_true",
        help="Emit GitHub Actions warning annotations for located findings to stderr",
    )
    parser.add_argument(
        "--step-summary",
        nargs="?",
        const="",
        help="Append Markdown review output to this file, or to GITHUB_STEP_SUMMARY when no path is supplied",
    )
    parser.add_argument(
        "--allow-comment-failure",
        action="store_true",
        help="Continue successfully if posting/updating the PR comment fails",
    )
    parser.add_argument(
        "--fail-on",
        choices=("Low", "Medium", "High"),
        help="Exit with status 1 when any finding has this severity or higher",
    )
    return parser


def validate_args(args: argparse.Namespace) -> None:
    if args.max_diff_chars < MIN_DIFF_CHARS:
        raise ReviewError(f"--max-diff-chars must be at least {MIN_DIFF_CHARS}")
    if args.update_comment:
        args.post_comment = True
    if args.prompt_only and args.post_comment:
        raise ReviewError("--prompt-only cannot be combined with --post-comment or --update-comment")
    if args.prompt_only and args.format != "markdown":
        raise ReviewError("--prompt-only writes a text prompt and requires --format markdown")
    if args.prompt_only and (args.github_annotations or args.step_summary is not None):
        raise ReviewError("--prompt-only cannot be combined with --github-annotations or --step-summary")
    if args.github_annotations and args.format != "markdown":
        raise ReviewError("--github-annotations requires --format markdown")
    if args.step_summary is not None and args.format != "markdown":
        raise ReviewError("--step-summary requires --format markdown")
    if args.allow_comment_failure and not args.post_comment:
        raise ReviewError("--allow-comment-failure requires --post-comment or --update-comment")
    if args.post_comment:
        if args.format != "markdown":
            raise ReviewError("--post-comment requires --format markdown")
        if not args.pr:
            raise ReviewError("--post-comment requires --pr")


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        validate_args(args)
        metadata, diff = load_inputs(args)
        if not diff.strip():
            raise ReviewError("Diff is empty")
        fail_review = False
        if args.prompt_only:
            output = review_prompt(metadata, diff, args.max_diff_chars)
        else:
            config = load_review_config(args.config, repo_root=args.repo_root)
            review = (
                build_llm_review(
                    metadata,
                    diff,
                    args.max_diff_chars,
                    args.llm_command,
                    repo_root=args.repo_root,
                    config=config,
                )
                if args.llm_command
                else build_review(
                    metadata,
                    diff,
                    args.max_diff_chars,
                    repo_root=args.repo_root,
                    config=config,
                )
            )
            validate_review(review)
            if args.format == "json":
                output = render_json(review)
            elif args.format == "sarif":
                output = render_sarif(review)
            else:
                output = render_markdown(review)
            if args.github_annotations:
                annotations = render_github_annotations(review)
                if annotations:
                    print(annotations, file=sys.stderr)
            if args.step_summary is not None:
                append_step_summary(args.step_summary or None, output)
            if args.post_comment:
                try:
                    post_comment(args.pr, output, update_existing=args.update_comment)
                except ReviewError as exc:
                    if not args.allow_comment_failure:
                        raise
                    print(f"claude-review: warning: {exc}", file=sys.stderr)
            fail_review = should_fail_review(review, args.fail_on)
        if args.output:
            Path(args.output).write_text(output, encoding="utf-8")
        else:
            print(output)
        if not args.prompt_only and fail_review:
            print(f"claude-review: failing because findings met --fail-on {args.fail_on}", file=sys.stderr)
            return 1
        return 0
    except ReviewError as exc:
        print(f"claude-review: error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
