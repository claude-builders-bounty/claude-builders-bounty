import json
import re
import shutil
import sqlite3
import subprocess
import tempfile
import textwrap
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
template = root / "skills/nextjs-sqlite-template/CLAUDE.md"
fixture = root / "tests/greenfield"


REQUIRED_TEMPLATE_CONTRACT = [
    "Next.js 15",
    "SQLite",
    "better-sqlite3",
    "migrations/",
    "Naming rules",
    "db:migrate",
    "What we do not do",
    'export const runtime = "nodejs"',
    "Definition of done",
]

LIST_ITEM = re.compile(r"^\s{0,3}(?:[-+*]|\d+[.)])\s+(.*)$")
FENCE = re.compile(r"^\s{0,3}(`{3,}|~{3,})(.*)$")
MARKDOWN_ONLY = re.compile(r"^\s{0,3}(?:=+|-+)\s*$")

# Declarative rules are identified by explicit obligation language.
OBLIGATION_LANGUAGE = re.compile(
    r"\b(?:must|shall|should|never|always|may not|required to|do not|don't)\b",
    re.IGNORECASE,
)
# Structural subjectless-imperative detection: a base-form verb followed
# by an object word. Catches arbitrary verbs not in any allowlist
# (e.g., "Obliterate", "Sanitize", "Purge"). The verb must not be a
# gerund (-ing), a modal, a pronoun, an article, a question word, or a
# common proper noun that happens to start a sentence as a subject.
# Words that can begin sentences but are not base-form verbs are listed
# in _NON_VERB_STARTERS; any other word starting a sentence or heading
# followed by an object is treated as a command regardless of its suffix
# or spelling, making the check robust to unknown verbs.
BASE_FORM_VERB_OBJECT = re.compile(
    r"^(?:(?:before|after|when|while|if|unless)\b[^,]*,\s*)?"
    r"(?P<verb>[A-Za-z][A-Za-z'-]+)"
    r"\s+(?P<object>[A-Za-z][A-Za-z'-]+)",
    re.IGNORECASE,
)
# Words that can begin sentences but are not base-form verbs:
# determiners, pronouns, modals, question words, coordinating
# conjunctions, common proper nouns used as sentence subjects, and
# common section-label words that describe topics rather than commands.
# Gerunds used as nouns (e.g., "understanding") and adjective-like
# section labels (e.g., "operational", "explanatory") are included
# as structural non-verbs rather than excluded by suffix heuristics.
_NON_VERB_STARTERS = frozenset({
    "a", "an", "the", "all", "every", "each", "some", "any", "no",
    "this", "that", "these", "those", "i", "me", "my", "myself",
    "you", "your", "yourself", "yourselves", "he", "him", "his",
    "himself", "she", "her", "herself", "it", "its", "itself",
    "we", "us", "our", "ours", "ourselves", "they", "them", "their",
    "theirs", "themselves", "can", "could", "may", "might", "must",
    "shall", "should", "will", "would", "what", "why", "how", "when",
    "where", "who", "which", "both", "few", "many", "most", "other",
    "another", "several", "either", "neither", "none", "one", "and",
    "but", "or", "nor", "so", "yet", "for", "sqlite", "code",
    "inline", "stack", "canonical", "database", "sql", "request",
    "patterns", "definition", "connection", "versions", "rules",
    "understanding", "operational", "explanatory", "contract", "naming",
})
# Head nouns that make a heading a conventional section label rather than a
# subjectless instruction. This is deliberately heading-specific: prose such
# as "Delete the strategy" must still be treated as a command. Matching the
# final word plus a recognized topic modifier captures noun phrases such as
# "Migration strategy" and "Database architecture" without allowing an
# imperative opener such as "Delete strategy" to masquerade as a label.
_SECTION_LABEL_HEADS = frozenset({
    "appendix", "architecture", "background", "commands", "concepts",
    "configuration", "considerations", "context", "contract", "conventions",
    "design", "example", "examples", "guide", "guidelines", "introduction",
    "migration", "migrations", "notes", "overview", "patterns", "policy",
    "reference", "rules", "schema", "stack", "strategy", "structure",
    "summary", "versions",
})
_SECTION_LABEL_MODIFIERS = frozenset({
    "api", "application", "component", "deployment", "development",
    "migration", "project", "runtime", "security", "server", "testing",
})
# Determiners that can serve as command objects (e.g., "every migration").
_DETERMINERS = frozenset({
    "a", "an", "the", "every", "each", "all", "this", "that",
    "these", "those", "our", "your", "any", "no", "some", "many",
    "most", "more", "much", "little", "few",
})
# Conjunctions and prepositions that are not command objects.
_CONJUNCTIONS_PREPOSITIONS = frozenset({
    "and", "or", "but", "nor", "so", "yet", "for", "of", "to",
    "in", "on", "at", "by", "with", "from", "up", "down", "out",
    "over", "under", "about", "between", "among", "through",
    "during", "without", "within", "before", "after", "since",
    "until", "while", "as", "like", "than", "into", "onto",
    "upon", "per", "via", "against", "toward", "along", "across",
    "around", "behind", "beyond", "except", "inside", "outside",
    "past", "till",
})


def markdown_contract_blocks(text: str) -> tuple[list[tuple[int, str, str]], bool]:
    """Return semantic Markdown text blocks outside code, plus fence validity."""
    blocks: list[tuple[int, str, str]] = []
    current: list[str] = []
    current_line = 0
    current_kind = ""
    fence_marker = ""
    fence_length = 0

    def flush() -> None:
        nonlocal current, current_line, current_kind
        if current:
            blocks.append(
                (current_line, " ".join(part.strip() for part in current), current_kind)
            )
            current = []
            current_line = 0
            current_kind = ""

    for number, raw_line in enumerate(text.splitlines(), 1):
        # Block quotes are prose, not code. Remove nested quote markers so
        # formatting cannot hide an instruction.
        line = re.sub(r"^\s{0,3}(?:>\s*)+", "", raw_line)
        fence = FENCE.match(line)
        if fence_marker:
            marker = fence.group(1) if fence else ""
            if (
                marker
                and marker[0] == fence_marker
                and len(marker) >= fence_length
                and not fence.group(2).strip()
            ):
                fence_marker = ""
                fence_length = 0
            continue
        if fence:
            flush()
            marker = fence.group(1)
            fence_marker = marker[0]
            fence_length = len(marker)
            continue
        if not line.strip() or MARKDOWN_ONLY.match(line):
            flush()
            continue
        heading = re.match(r"^\s{0,3}#{1,6}\s+(.*?)\s*#*\s*$", line)
        if heading:
            flush()
            # Headings are text too: labels naturally pass the semantic rule
            # check, while imperative or obligation-bearing headings do not.
            blocks.append((number, heading.group(1), "heading"))
            continue
        indented = raw_line.startswith("    ") or raw_line.startswith("\t")
        if indented:
            # A wrapped list continuation can carry its Reason. Other
            # four-space/tab-indented blocks are Markdown code examples.
            if current_kind == "list":
                current.append(line)
            else:
                flush()
            continue
        item = LIST_ITEM.match(line)
        if item:
            flush()
            current_line = number
            current_kind = "list"
            current = [item.group(1)]
            continue
        if not current_line:
            current_line = number
            current_kind = "prose"
        current.append(line)

    flush()
    return blocks, not fence_marker


def validate_template_text(text: str) -> None:
    missing = [item for item in REQUIRED_TEMPLATE_CONTRACT if item not in text]
    assert not missing, f"missing template contract: {missing}"
    assert "API routes are cached by default" not in text
    assert "Always close connections" not in text

    rules_without_reasons = []
    blocks, fences_closed = markdown_contract_blocks(text)
    for number, block, kind in blocks:
        # Inline code is example syntax. Replace it with a neutral subject
        # token, rather than deleting it and making explanatory text such as
        # "`SQLite` uses ..." look subjectless.
        prose = re.sub(r"(`+).*?\1", "CODE", block).strip()
        if not prose:
            continue
        has_reason = bool(re.search(r"\bReason\s*:", prose, re.IGNORECASE))
        explanatory_heading = kind == "heading" and bool(
            re.match(r"^(?:what|why|how|when|where)\b", prose, re.IGNORECASE)
        )
        object_command = BASE_FORM_VERB_OBJECT.match(prose)
        # Structural subjectless-imperative detection: a word that
        # starts a sentence or heading is a command verb if it is
        # not a known non-verb (determiner, pronoun, modal, question
        # word, common noun, or section label). This catches arbitrary
        # verbs without suffix heuristics or finite verb lists.
        words = re.findall(r"[A-Za-z][A-Za-z'-]*", prose.lower())
        first_word = words[0] if words else ""
        section_label = bool(
            kind == "heading"
            and words
            and words[-1] in _SECTION_LABEL_HEADS
            and (
                len(words) == 1
                or first_word in _NON_VERB_STARTERS
                or first_word in _SECTION_LABEL_MODIFIERS
            )
            and not any(word in _DETERMINERS for word in words[1:])
            and not OBLIGATION_LANGUAGE.search(prose)
        )
        # Standalone imperative: a single word that is not a known non-verb.
        # Headings also allow a trailing colon, so heading punctuation cannot
        # hide an enforceable command; a prose label such as "Example:" remains
        # distinct from the existing one-word prose-command form.
        standalone_pattern = (
            r"^[A-Za-z][A-Za-z'-]*[.:]?$"
            if kind == "heading"
            else r"^[A-Za-z][A-Za-z'-]*\.?$"
        )
        standalone_imperative = bool(
            re.match(standalone_pattern, prose)
        ) and first_word not in _NON_VERB_STARTERS
        if kind == "heading":
            # Headings with determiner objects are commands.
            # Headings where the opening word is not a known non-verb
            # are also commands. Known non-verb section labels are preserved.
            object_is_target = (
                first_word in _DETERMINERS or first_word not in _NON_VERB_STARTERS
            )
        else:
            object_is_target = first_word not in _CONJUNCTIONS_PREPOSITIONS
        arbitrary_imperative = bool(
            object_command
            and first_word not in _NON_VERB_STARTERS
            and object_is_target
        )
        enforceable = not explanatory_heading and bool(
            OBLIGATION_LANGUAGE.search(prose)
            or (arbitrary_imperative and not section_label)
            or (standalone_imperative and not section_label)
        )
        if enforceable and not has_reason:
            rules_without_reasons.append((number, block))

    assert fences_closed, "unclosed Markdown code fence"
    assert not rules_without_reasons, (
        f"rules without explicit reasons: {rules_without_reasons}"
    )


def compact_typescript(source: str) -> str:
    return re.sub(r"\s+", " ", source).strip()


def prove_route_behavior(project: Path) -> None:
    """Execute the checked-in TS route through validation, service, and query."""
    proof_value = f"db-proof-{uuid.uuid4()}"
    proof_owner = 1000 + uuid.uuid4().int % 1_000_000
    absent_owner = proof_owner + 1
    proof_project = 1000 + uuid.uuid4().int % 1_000_000
    proof_created_at = f"proof-time-{uuid.uuid4()}"
    with tempfile.TemporaryDirectory(prefix="b2-route-proof-") as temp:
        harness = Path(temp)
        next_shim = harness / "next-server.mjs"
        zod_shim = harness / "zod.mjs"
        sqlite_shim = harness / "better-sqlite3.mjs"
        loader = harness / "loader.mjs"
        runner = harness / "runner.mjs"

        next_shim.write_text(
            "export const NextResponse = { json(body, init = {}) { "
            "return Response.json(body, init); } };\n"
        )
        zod_shim.write_text(textwrap.dedent("""
            class NumberSchema {
              constructor() { this.integer = false; this.positiveOnly = false; }
              int() { this.integer = true; return this; }
              positive() { this.positiveOnly = true; return this; }
              parse(value) {
                const parsed = Number(value);
                if (!Number.isFinite(parsed)) throw new Error("not a number");
                if (this.integer && !Number.isInteger(parsed)) throw new Error("not an integer");
                if (this.positiveOnly && parsed <= 0) throw new Error("not positive");
                return parsed;
              }
            }
            export const z = {
              coerce: { number: () => new NumberSchema() },
              object(shape) {
                return { safeParse(input) {
                  try {
                    const data = {};
                    for (const [key, schema] of Object.entries(shape)) data[key] = schema.parse(input[key]);
                    return { success: true, data };
                  } catch (error) { return { success: false, error }; }
                } };
              },
            };
        """).strip() + "\n")
        sqlite_shim.write_text(textwrap.dedent("""
            import { DatabaseSync } from "node:sqlite";
            export default class Database {
              constructor(path) { this.inner = new DatabaseSync(path); }
              exec(sql) { return this.inner.exec(sql); }
              prepare(sql) { return this.inner.prepare(sql); }
              pragma(value) { return this.inner.exec(`PRAGMA ${value}`); }
            }
        """).strip() + "\n")
        loader.write_text(textwrap.dedent(f"""
            import {{ existsSync }} from "node:fs";
            import {{ registerHooks }} from "node:module";
            import {{ pathToFileURL }} from "node:url";
            const project = {json.dumps(str(project))};
            const shims = {{
              "next/server": {json.dumps(next_shim.as_uri())},
              "zod": {json.dumps(zod_shim.as_uri())},
              "better-sqlite3": {json.dumps(sqlite_shim.as_uri())},
            }};
            registerHooks({{
              resolve(specifier, context, nextResolve) {{
                if (shims[specifier]) return {{ url: shims[specifier], shortCircuit: true }};
                if (specifier.startsWith("@/")) {{
                  const base = `${{project}}/${{specifier.slice(2)}}`;
                  const target = existsSync(`${{base}}.ts`) ? `${{base}}.ts` : `${{base}}/index.ts`;
                  return {{ url: pathToFileURL(target).href, shortCircuit: true }};
                }}
                return nextResolve(specifier, context);
              }},
            }});
        """).strip() + "\n")
        runner.write_text(textwrap.dedent(f"""
            import {{ db }} from {json.dumps((project / "lib/db/index.ts").as_uri())};
            import {{ GET }} from {json.dumps((project / "app/api/projects/route.ts").as_uri())};
            db.exec({json.dumps((project / "migrations/0001_initial.sql").read_text())});
            db.prepare("INSERT INTO users (id, email, created_at) VALUES (?, ?, ?)")
              .run({proof_owner}, "proof@example.test", {json.dumps(proof_created_at)});
            db.prepare("INSERT INTO projects (id, owner_id, name, created_at) VALUES (?, ?, ?, ?)")
              .run({proof_project}, {proof_owner}, {json.dumps(proof_value)}, {json.dumps(proof_created_at)});

            const valid = await GET(new Request("https://example.test/api/projects?ownerId={proof_owner}"));
            const validBody = await valid.json();
            if (valid.status !== 200 || JSON.stringify(validBody) !== JSON.stringify({{
              projects: [{{ id: {proof_project}, ownerId: {proof_owner}, name: {json.dumps(proof_value)}, createdAt: {json.dumps(proof_created_at)} }}],
            }})) throw new Error(`valid route result was not database-backed: ${{valid.status}} ${{JSON.stringify(validBody)}}`);

            const absent = await GET(new Request("https://example.test/api/projects?ownerId={absent_owner}"));
            if (absent.status !== 200 || JSON.stringify(await absent.json()) !== JSON.stringify({{ projects: [] }}))
              throw new Error("owner filter did not reach the query");

            for (const ownerId of ["not-an-id", "0", "1.5"]) {{
              const invalid = await GET(new Request(`https://example.test/api/projects?ownerId=${{ownerId}}`));
              if (invalid.status !== 400 || JSON.stringify(await invalid.json()) !== JSON.stringify({{ error: "invalid_request" }}))
                throw new Error(`validation accepted invalid ownerId ${{ownerId}}`);
            }}
        """).strip() + "\n")
        result = subprocess.run(
            ["node", "--experimental-strip-types", "--import", str(loader), str(runner)],
            text=True,
            capture_output=True,
            timeout=20,
        )
        assert result.returncode == 0, (
            "route -> validation -> service -> query behavioral proof failed:\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )


def validate_project_architecture(project: Path) -> None:
    package = json.loads((project / "package.json").read_text())
    tsconfig = json.loads((project / "tsconfig.json").read_text())
    assert package["dependencies"]["next"].startswith("15.")
    assert "better-sqlite3" in package["dependencies"]
    assert tsconfig["compilerOptions"]["strict"] is True

    expected_paths = [
        "migrations/0001_initial.sql",
        "lib/db/index.ts",
        "lib/db/queries/projects.ts",
        "lib/validation/project.ts",
        "lib/services/project.ts",
        "app/api/projects/route.ts",
        "CONTEXT_CHECK.md",
    ]
    absent = [path for path in expected_paths if not (project / path).is_file()]
    assert not absent, f"fresh-project evidence missing paths: {absent}"

    route = (project / "app/api/projects/route.ts").read_text()
    query = (project / "lib/db/queries/projects.ts").read_text()
    service = (project / "lib/services/project.ts").read_text()
    migration = (project / "migrations/0001_initial.sql").read_text()
    context_check = (project / "CONTEXT_CHECK.md").read_text()

    assert 'export const runtime = "nodejs"' in route
    assert 'from "@/lib/services/project"' in route
    assert 'from "@/lib/validation/project"' in route
    assert "@/lib/db" not in route
    assert "listProjects(parsed.data.ownerId)" in compact_typescript(route)

    assert 'from "@/lib/db"' in query
    assert ".prepare(" in query and "SELECT *" not in query
    assert ".all(ownerId)" in compact_typescript(query)

    # Prove the middle architectural layer is real rather than merely present:
    # the route's service must delegate its only function body to the query
    # layer with the validated owner id. Exact body matching rejects fabricated
    # success-shaped fallback data and dead-code imports.
    compact_service = compact_typescript(service)
    expected_service = (
        'import { listProjectsByOwner } from "@/lib/db/queries/projects"; '
        "export function listProjects(ownerId: number) { "
        "return listProjectsByOwner(ownerId); }"
    )
    assert compact_service == expected_service, (
        "project service must directly delegate to the query layer without "
        "fallback data"
    )

    assert "ON DELETE CASCADE" in migration
    assert "idx_projects_owner_id" in migration
    assert "NO_CLARIFICATION_NEEDED" in context_check

    # Execute the actual TypeScript modules with narrowly scoped dependency
    # shims. Random database content prevents hard-coded route/query results
    # from satisfying the proof.
    prove_route_behavior(project)

    # Apply the checked-in migration to an actual empty SQLite database and
    # exercise its foreign-key policy and indexed query shape.
    database_path = project / "data" / "proof.db"
    database_path.parent.mkdir(exist_ok=True)
    connection = sqlite3.connect(database_path)
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(migration)
        connection.execute(
            "INSERT INTO users (id, email, created_at) VALUES (?, ?, ?)",
            (1, "owner@example.test", "2026-09-21T00:00:00Z"),
        )
        connection.execute(
            "INSERT INTO projects (id, owner_id, name, created_at) VALUES (?, ?, ?, ?)",
            (1, 1, "Proof project", "2026-09-21T00:00:00Z"),
        )
        plan = connection.execute(
            "EXPLAIN QUERY PLAN SELECT id, owner_id, name, created_at "
            "FROM projects WHERE owner_id = ? ORDER BY id",
            (1,),
        ).fetchall()
        assert any("idx_projects_owner_id" in row[3] for row in plan), plan
        connection.execute("DELETE FROM users WHERE id = ?", (1,))
        remaining = connection.execute(
            "SELECT count(*) FROM projects"
        ).fetchone()[0]
        assert remaining == 0
    finally:
        connection.close()


def validate() -> None:
    text = template.read_text()
    validate_template_text(text)

    # Recreate a fresh project in a new directory, then paste the template
    # exactly as the acceptance criterion describes. The fixture has no
    # dependencies or generated output, so this proof installs nothing.
    with tempfile.TemporaryDirectory(prefix="nextjs-sqlite-greenfield-") as temp:
        project = Path(temp) / "new-project"
        shutil.copytree(fixture, project, ignore=shutil.ignore_patterns("CLAUDE.md"))
        shutil.copy2(template, project / "CLAUDE.md")
        assert (project / "CLAUDE.md").read_bytes() == template.read_bytes()
        validate_project_architecture(project)

    # Keep the checked-in pasted copy reviewable and byte-identical to source.
    assert (fixture / "CLAUDE.md").read_bytes() == template.read_bytes(), (
        "tests/greenfield/CLAUDE.md must be an unmodified paste of the template"
    )


if __name__ == "__main__":
    validate()
    print("template contract validation: PASS")
    print("fresh-project paste and architecture validation: PASS")
