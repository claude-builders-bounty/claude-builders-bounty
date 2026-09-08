"""Offline snapshot parsing, evidence-grounded scanning, and report rendering."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

MAX_METADATA_BYTES = 1_048_576
MAX_FILES_BYTES = 4_194_304
MAX_DIFF_BYTES = 1_048_576
MAX_OUTPUT_BYTES = 49_152
MAX_EVIDENCE_CHARS = 240
MAX_FINDINGS = 24
SEVERITY_ORDER = {"high": 0, "medium": 1, "low": 2, "informational": 3}


class ReviewError(Exception):
    """A controlled review failure; the message is safe to show on stderr."""

    exit_code = 1


class InputValidationError(ReviewError):
    exit_code = 4


class MissingSnapshotError(ReviewError):
    exit_code = 3


class EmptyDiffError(ReviewError):
    exit_code = 5


class InvalidPRUrlError(ReviewError):
    exit_code = 2


class OutputValidationError(ReviewError):
    exit_code = 6


@dataclass(frozen=True)
class PullRef:
    owner: str
    repo: str
    number: int

    @property
    def canonical_url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}/pull/{self.number}"


@dataclass(frozen=True)
class FileChange:
    filename: str
    status: str
    additions: int
    deletions: int
    previous_filename: str | None = None
    binary: bool = False
    renamed: bool = False


@dataclass(frozen=True)
class DiffLine:
    marker: str
    text: str
    old_number: int | None
    new_number: int | None


@dataclass(frozen=True)
class Hunk:
    path: str
    header: str
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    lines: tuple[DiffLine, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class ReviewData:
    ref: PullRef
    title: str
    head_sha: str
    base_sha: str
    metadata_updated_at: str
    files: tuple[FileChange, ...]
    hunks: dict[str, tuple[Hunk, ...]]


def parse_pr_url(url: str) -> PullRef:
    """Accept only an HTTPS github.com pull-request URL."""

    if not isinstance(url, str):
        raise InvalidPRUrlError("Invalid PR URL: expected one string.")
    parsed = url.split("?", 1)[0].split("#", 1)[0].rstrip("/")
    parts = parsed.split("/")
    if (
        len(parts) != 7
        or parts[0] != "https:"
        or parts[1] != ""
        or parts[2].lower() not in {"github.com", "www.github.com"}
        or not parts[3]
        or not parts[4]
        or parts[5] != "pull"
    ):
        raise InvalidPRUrlError("Invalid PR URL. Use https://github.com/OWNER/REPO/pull/NUMBER")
    owner, repo = parts[3], parts[4]
    if owner in {"", ".", ".."} or repo in {"", ".", ".."} or not _safe_component(owner) or not _safe_component(repo):
        raise InvalidPRUrlError("Invalid PR URL: owner or repository is malformed.")
    if not re.fullmatch(r"[1-9][0-9]*", parts[6]):
        raise InvalidPRUrlError("Invalid PR URL: NUMBER must be a positive integer.")
    return PullRef(owner, repo, int(parts[6]))


def _safe_component(value: str) -> bool:
    return not any(ch in value for ch in "\r\n\t /\\") and value not in {"api", "raw"}


def _read_limited(path: Path, limit: int, label: str) -> bytes:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        raise MissingSnapshotError(f"Offline context is missing {label}.") from None
    except OSError:
        raise MissingSnapshotError(f"Offline context cannot be read: {label}.") from None
    if len(raw) > limit:
        raise InputValidationError(f"Oversized {label}: {len(raw)} bytes exceeds limit {limit}.")
    return raw


def _load_json(raw: bytes, label: str):
    try:
        return json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        raise InputValidationError(f"Malformed JSON in {label}.") from None


def _file_from_record(record: dict, index: int) -> FileChange:
    if not isinstance(record, dict) or not isinstance(record.get("filename"), str):
        raise InputValidationError(f"Malformed file record at index {index}.")
    filename = record["filename"].replace("\\", "/")
    if not filename or filename.startswith("/") or ".." in filename.split("/"):
        raise InputValidationError(f"Unsafe changed-file path at index {index}.")
    try:
        additions = int(record.get("additions", 0))
        deletions = int(record.get("deletions", 0))
    except (TypeError, ValueError):
        raise InputValidationError(f"Malformed change counts for {filename}.") from None
    if additions < 0 or deletions < 0:
        raise InputValidationError(f"Negative change counts for {filename}.")
    status = record.get("status")
    if status is not None and not isinstance(status, str):
        raise InputValidationError(f"Malformed status for {filename}.")
    previous = record.get("previous_filename")
    if previous is not None and not isinstance(previous, str):
        raise InputValidationError(f"Malformed previous filename for {filename}.")
    return FileChange(
        filename,
        status or "changed",
        additions,
        deletions,
        previous,
        bool(record.get("binary", False)),
        status == "renamed" or previous is not None,
    )


def parse_metadata(raw: bytes, ref: PullRef) -> tuple[str, str, str, str]:
    data = _load_json(raw, "metadata.json")
    if not isinstance(data, dict) or data.get("number") != ref.number:
        raise InputValidationError("metadata.json does not match the requested PR.")
    html_url = data.get("html_url")
    if html_url is not None and parse_pr_url(html_url) != ref:
        raise InputValidationError("metadata.json URL does not match the requested PR.")
    head = data.get("head", {})
    base = data.get("base", {})
    if not isinstance(head, dict) or not isinstance(base, dict):
        raise InputValidationError("Malformed head/base metadata.")
    sha_pattern = re.compile(r"[0-9a-fA-F]{7,40}")
    head_sha, base_sha = head.get("sha"), base.get("sha")
    if not isinstance(head_sha, str) or not sha_pattern.fullmatch(head_sha):
        raise InputValidationError("metadata.json has an invalid head SHA.")
    if not isinstance(base_sha, str) or not sha_pattern.fullmatch(base_sha):
        raise InputValidationError("metadata.json has an invalid base SHA.")
    title = data.get("title")
    metadata_updated_at = data.get("updated_at")
    if not isinstance(metadata_updated_at, str) or not metadata_updated_at:
        raise InputValidationError("metadata.json is missing an updated_at timestamp.")
    return (
        title if isinstance(title, str) else f"Pull request #{ref.number}",
        head_sha,
        base_sha,
        metadata_updated_at,
    )


def parse_files(raw: bytes) -> tuple[FileChange, ...]:
    data = _load_json(raw, "files.json")
    if not isinstance(data, list):
        raise InputValidationError("files.json must contain an array.")
    return tuple(_file_from_record(record, index) for index, record in enumerate(data))


def parse_diff(diff: str, records: Iterable[FileChange]) -> tuple[dict[str, tuple[Hunk, ...]], tuple[FileChange, ...]]:
    """Parse a unified GitHub multi-file diff and retain exact hunk anchors."""

    if not diff.strip():
        raise EmptyDiffError("The pull request diff is empty.")
    if "\x00" in diff:
        raise InputValidationError("Malformed diff contains a NUL byte.")
    known = {item.filename: item for item in records}
    hunks: dict[str, list[Hunk]] = {name: [] for name in known}
    current_path: str | None = None
    current_lines: list[DiffLine] = []
    current_hunk: Hunk | None = None
    hunk_re = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@(.*)$")
    old_no = new_no = 0

    def finish_hunk() -> None:
        nonlocal current_hunk, current_lines
        if current_hunk is not None:
            current_hunk = Hunk(
                current_hunk.path,
                current_hunk.header,
                current_hunk.old_start,
                current_hunk.old_count,
                current_hunk.new_start,
                current_hunk.new_count,
                tuple(current_lines),
            )
            hunks.setdefault(current_hunk.path, []).append(current_hunk)
        current_lines = []
        current_hunk = None

    for line in diff.splitlines():
        if line.startswith("diff --git "):
            finish_hunk()
            payload = line[len("diff --git ") :]
            if " b/" not in payload:
                raise InputValidationError("Malformed diff header is missing destination path.")
            source, destination = payload.split(" b/", 1)
            destination = destination[2:] if destination.startswith("b/") else destination
            source = source[2:] if source.startswith("a/") else source
            current_path = destination or source
            hunks.setdefault(current_path, [])
            old_no = new_no = 0
            continue
        if current_path is None:
            raise InputValidationError("Diff content appears before a diff --git header.")
        match = hunk_re.match(line)
        if match:
            finish_hunk()
            old_start = int(match.group(1))
            old_count = int(match.group(2) or "1")
            new_start = int(match.group(3))
            new_count = int(match.group(4) or "1")
            current_hunk = Hunk(
                current_path,
                f"@@ -{old_start},{old_count} +{new_start},{new_count} @@",
                old_start,
                old_count,
                new_start,
                new_count,
            )
            old_no, new_no = old_start, new_start
            continue
        if current_hunk is None:
            continue
        if line.startswith("@@"):
            raise InputValidationError(f"Malformed hunk header in {current_path}.")
        if line.startswith("+"):
            current_lines.append(DiffLine("+", line[1:], None, new_no))
            new_no += 1
        elif line.startswith("-"):
            current_lines.append(DiffLine("-", line[1:], old_no, None))
            old_no += 1
        elif line.startswith("\\") or line == "No newline at end of file":
            continue
        elif line.startswith(" ") or line == "":
            current_lines.append(DiffLine(" ", line[1:], old_no, new_no))
            old_no += 1
            new_no += 1
        else:
            raise InputValidationError(f"Malformed diff line in {current_path}.")
    finish_hunk()

    merged = dict(known)
    for path in hunks:
        if path not in merged:
            merged[path] = FileChange(path, "changed", 0, 0)
    return {path: tuple(items) for path, items in hunks.items()}, tuple(merged.values())


def _evidence(text: str) -> str:
    clean = "".join(char if char.isprintable() and char != "\t" else " " for char in text.strip())
    clean = re.sub(r" +", " ", clean)
    if len(clean) > MAX_EVIDENCE_CHARS:
        return clean[: MAX_EVIDENCE_CHARS - 20] + " …[evidence truncated]"
    return clean


def _outside_quoted_text(match: re.Match, line: str) -> bool:
    """Reject common pattern mentions inside a single-line string literal."""

    before = line[: match.start()]
    return (before.count('"') + before.count("'")) % 2 == 0


def scan(data: ReviewData) -> list[dict]:
    findings: list[dict] = []

    def add(severity: str, path: str, anchor: str, evidence: str, why: str, change: str, rule: str) -> None:
        findings.append(
            {
                "severity": severity,
                "path": path,
                "anchor": anchor,
                "evidence": _evidence(evidence),
                "why": why,
                "change": change,
                "rule": rule,
            }
        )

    rules = [
        ("shell_true", re.compile(r"\bsubprocess\.\w+\s*\([^)]*shell\s*=\s*True"), "high",
         "Shell invocation is enabled on changed lines.",
         "Process arguments can cross a shell parser and increase command-injection impact.",
         "Avoid shell=True or pass a fully validated argument array after reviewing every input source."),
        ("dynamic_execution", re.compile(r"\b(?:eval|exec)\s*\(|\bos\.system\s*\("), "high",
         "The diff adds dynamic execution.",
         "Dynamically evaluated strings can turn untrusted input into executable code.",
         "Replace dynamic execution with explicit operations or parse untrusted input into a safe structure."),
        ("dotfile_secret", re.compile(r"open\s*\([^)]*(?:\.bashrc|\.zshrc|\.profile|\.netrc|\.ssh)", re.I), "high",
         "Changed code reads a user dotfile.",
         "Reading shell or account configuration can expose unrelated credentials and private settings.",
         "Remove dotfile credential discovery and require explicit, secret-manager-provided configuration."),
        ("hardcoded_secret", re.compile(r"(?:api[_-]?key|secret|password|token)[\"']?\s*[:=]\s*[\"'][^\"']+", re.I), "high",
         "A changed assignment resembles a hardcoded credential.",
         "Literal-looking secrets can persist in history and leak to anyone with repository access.",
         "Verify the value is non-sensitive; otherwise revoke it and load it from an approved runtime source."),
        ("broad_except", re.compile(r"\bexcept\s+(?:Exception|BaseException)\b(?:\s+as\s+\w+)?\s*:|\bexcept\s*:\b"), "medium",
         "A changed line adds a broad exception handler.",
         "Broad handling can hide failures and make recovery behavior unpredictable.",
         "Catch the narrow expected exception and preserve diagnostics at the operation boundary."),
        ("github_event_interpolation", re.compile(r"\$\{\{\s*github\.event\."), "medium",
         "A changed workflow line interpolates a github.event property.",
         "Direct interpolation into a run script can allow attacker-controlled text to reach the shell.",
         "Pass the value through a quoted environment variable instead of interpolating it into shell code."),
        ("workflow_write_permission", re.compile(r"^\s*(pull-requests|issues|contents):\s*write\s*$"), "medium",
         "A changed workflow grants write permission.",
         "Excess workflow permissions broaden the effect of a compromised review job.",
         "Limit the workflow token to the single permission required by the automated action."),
    ]

    for path, hunks in data.hunks.items():
        for hunk in hunks:
            anchor = f"hunk {hunk.header}"
            for line in hunk.lines:
                if line.marker != "+":
                    continue
                for rule, pattern, severity, observed, why, change in rules:
                    match = pattern.search(line.text)
                    if match and _outside_quoted_text(match, line.text):
                        if rule in {"shell_true", "dynamic_execution", "broad_except"} and not path.endswith(".py"):
                            continue
                        if rule in {"github_event_interpolation", "workflow_write_permission"} and not path.endswith((".yml", ".yaml")):
                            continue
                        add(severity, path, f"{anchor}; new line {line.new_number}", line.text, why, change, rule)
                        break

    for item in data.files:
        item_hunks = data.hunks.get(item.filename, ())
        if item.binary:
            add(
                "informational",
                item.filename,
                "binary marker",
                f"Changed-file record marks this path binary; content was not decoded ({item.status}).",
                "Binary changes cannot be evaluated by static line scanning.",
                "Inspect the rendered binary artifact outside this report.",
                "binary",
            )
        elif item.renamed and not item_hunks:
            add(
                "informational",
                item.filename,
                "rename marker",
                f"The record marks this path renamed from {item.previous_filename or 'an unavailable source'}.",
                "No hunk is available, so unchanged-file equivalence cannot be proven.",
                "Compare rename detection with source-control history.",
                "rename",
            )
        elif item.additions + item.deletions > 0 and not item_hunks:
            add(
                "medium",
                item.filename,
                "missing hunk",
                f"The record reports +{item.additions}/-{item.deletions}, but no unified hunk was available.",
                "Changed content is incomplete, so no definitive content finding can be made.",
                "Obtain the complete diff before assessing this path.",
                "missing_hunk",
            )

    unique = {(x["path"], x["anchor"], x["rule"], x["evidence"]): x for x in findings}

    def finding_key(item: dict) -> tuple:
        line_match = re.search(r"new line (\d+)$", item["anchor"])
        line_number = int(line_match.group(1)) if line_match else -1
        return (SEVERITY_ORDER[item["severity"]], item["path"], item["anchor"], line_number, item["rule"], item["evidence"])

    return sorted(
        unique.values(),
        key=finding_key,
    )


def _confidence(findings: list[dict]) -> str:
    if any(item["severity"] == "high" for item in findings):
        return "Medium"
    incomplete = any(item["rule"] in {"missing_hunk", "binary", "rename"} for item in findings)
    return "Medium" if incomplete or len(findings) > 6 else "High"


def _summary(data: ReviewData) -> str:
    additions = sum(item.additions for item in data.files)
    deletions = sum(item.deletions for item in data.files)
    hunk_count = sum(len(items) for items in data.hunks.values())
    first = f"The pull request changes {len(data.files)} files, with {additions} lines added and {deletions} lines removed."
    second = (
        f"Static analysis inspected {hunk_count} changed hunks and reports only content visible in those "
        "changed lines; unavailable context is marked uncertain."
    )
    return f"{first} {second}"


def render_report(data: ReviewData) -> str:
    findings = scan(data)
    truncation_note = ""
    if len(findings) > MAX_FINDINGS:
        omitted = len(findings) - MAX_FINDINGS
        findings = findings[:MAX_FINDINGS]
        truncation_note = f"- [Output truncated: {omitted} lower-priority finding(s) omitted by the deterministic limit.]"

    lines = ["## Summary of changes", _summary(data), "", "## Identified risks"]
    if findings:
        for finding in findings:
            lines.extend(
                [
                    f"- **{finding['severity'].capitalize()}** — `{finding['path']}` — `{finding['anchor']}`",
                    f"  - Observed evidence: `{finding['evidence']}`",
                    f"  - Why it matters: {finding['why']}",
                    f"  - Suggested check or change: {finding['change']}",
                ]
            )
    else:
        lines.append("- No changed-line pattern matched the deterministic static rules.")
    if truncation_note:
        lines.append(truncation_note)

    lines.extend(["", "## Improvement suggestions"])
    changes = list(dict.fromkeys(item["change"] for item in findings))
    lines.extend(f"- {item}" for item in changes)
    if not changes:
        lines.append("- No evidence-grounded change is available beyond validating the diff in context.")

    confidence = _confidence(findings)
    lines.extend(
        [
            "",
            "## Confidence score",
            f"Confidence score: {confidence}. This is deterministic and static review, not a paid-model or exhaustive expert audit.",
            "",
        ]
    )
    report = "\n".join(lines)
    if len(report.encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise OutputValidationError("Rendered report exceeds the configured hard output cap.")
    return report


def validate_report(report: str) -> None:
    expected = [
        "## Summary of changes",
        "## Identified risks",
        "## Improvement suggestions",
        "## Confidence score",
    ]
    headings = re.findall(r"^## .+$", report, re.MULTILINE)
    if headings != expected:
        raise OutputValidationError("Internal output validation failed: report headings are invalid.")
    body = report.split("## Summary of changes", 1)[1].split("## Identified risks", 1)[0].strip()
    sentences = [part for part in re.findall(r"[^.!?]+[.!?]", body) if part.strip()]
    if not 2 <= len(sentences) <= 3:
        raise OutputValidationError("Internal output validation failed: summary sentence count is invalid.")
    score = re.findall(r"Confidence score: (Low|Medium|High)\b", report)
    if len(score) != 1:
        raise OutputValidationError("Internal output validation failed: confidence vocabulary is invalid.")


def load_offline(ref: PullRef, context_dir: Path) -> ReviewData:
    if not context_dir.is_dir():
        raise MissingSnapshotError("Offline context directory does not exist.")
    metadata_raw = _read_limited(context_dir / "metadata.json", MAX_METADATA_BYTES, "metadata.json")
    files_raw = _read_limited(context_dir / "files.json", MAX_FILES_BYTES, "files.json")
    diff_raw = _read_limited(context_dir / "pr.diff", MAX_DIFF_BYTES, "pr.diff")
    title, head_sha, base_sha, metadata_updated_at = parse_metadata(metadata_raw, ref)
    files = parse_files(files_raw)
    try:
        diff = diff_raw.decode("utf-8")
    except UnicodeDecodeError:
        raise InputValidationError("Malformed diff: pr.diff is not UTF-8 text.") from None
    hunks, merged_files = parse_diff(diff, files)
    return ReviewData(
        ref,
        title,
        head_sha,
        base_sha,
        metadata_updated_at,
        merged_files,
        hunks,
    )
