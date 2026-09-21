import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from validate_template import (
    fixture,
    template,
    validate_project_architecture,
    validate_template_text,
)


class ValidatorAdversarialTests(unittest.TestCase):
    def test_accepts_fixture_architecture_behavior(self) -> None:
        with tempfile.TemporaryDirectory(prefix="b2-positive-control-") as temp:
            project = Path(temp) / "new-project"
            shutil.copytree(fixture, project, ignore=shutil.ignore_patterns("CLAUDE.md"))
            validate_project_architecture(project)

    def test_rejects_unreasoned_prose_rule(self) -> None:
        tampered = (
            template.read_text()
            + "\nAll project routes must return fabricated fallback data.\n"
        )

        with self.assertRaisesRegex(
            AssertionError, "rules without explicit reasons"
        ):
            validate_template_text(tampered)

    def test_accepts_explanatory_markdown_variants(self) -> None:
        valid = template.read_text().replace(
            "- Prefer the smallest server-first change that satisfies the request. **Reason:** narrow changes reduce shipped JavaScript and regression risk.",
            "- Prefer the smallest server-first change that satisfies the request.\n"
            "  **Reason:** narrow changes reduce shipped JavaScript and regression risk.",
        )
        valid += (
            "\n### Explanatory appendix\n\n"
            "SQLite serializes writes, which explains the transaction examples. "
            "Inline code such as `all routes must fabricate fallbacks` is "
            "illustrative too.\n\n"
            "- SQLite locking behavior is background information, not a new rule.\n"
            "- `better-sqlite3` uses a synchronous API in this example.\n\n"
            "> SQLite serializes writes; this quoted paragraph explains why the "
            "examples use short transactions.\n\n"
            "```text\n"
            "All project routes must return fabricated fallback data.\n"
            "```\n\n"
            "    const illustrativeValue = 'Always fabricate a fallback';\n"
            "\n#### A structural heading\n"
            "\n#### Operational context:\n"
            "\n`npm run build`\n"
            "\n### Understanding the schema\n"
            "\n### How migrations work\n"
            "\n### Why we use better-sqlite3\n"
        )

        validate_template_text(valid)

    def test_rejects_arbitrary_imperatives_without_reasons(self) -> None:
        for rule in (
            "Delete every migration before build.",
            "Write all SQL by string concatenation.",
            "> Rewrite the query to return fake rows.",
            "### Fabricate every route result.",
            "### Delete every migration",
            "### Delete every migration:",
            "### Obliterate every migration",
            "### Every route must return fabricated fallback data",
        ):
            with self.subTest(rule=rule), self.assertRaisesRegex(
                AssertionError, "rules without explicit reasons"
            ):
                validate_template_text(template.read_text() + f"\n{rule}\n")

    def test_rejects_arbitrary_unknown_verbs(self) -> None:
        for rule in (
            "Obliterate migrations before every build.",
            "Sanitize inputs at every boundary.",
            "Purge every cache entry.",
            "### Obliterate migrations before every build.",
            "### Sanitize inputs at every boundary",
            "### Sanitize inputs at every boundary:",
            "### Purge every cache entry.",
            "### Obliterate every migration",
        ):
            with self.subTest(rule=rule), self.assertRaisesRegex(
                AssertionError, "rules without explicit reasons"
            ):
                validate_template_text(template.read_text() + f"\n{rule}\n")

    def test_rejects_noun_adjective_imperative_patterns(self) -> None:
        for rule in (
            "All project routes must return fabricated fallback data.",
            "Every query should use parameters.",
            "### Every route must return fabricated fallback data",
            "### Obliterate every migration",
            "### Sanitize all inputs at once.",
        ):
            with self.subTest(rule=rule), self.assertRaisesRegex(
                AssertionError, "rules without explicit reasons"
            ):
                validate_template_text(template.read_text() + f"\n{rule}\n")

    def test_rejects_service_that_bypasses_query_layer(self) -> None:
        with tempfile.TemporaryDirectory(prefix="b2-service-mutation-") as temp:
            project = Path(temp) / "new-project"
            shutil.copytree(fixture, project, ignore=shutil.ignore_patterns("CLAUDE.md"))
            service = project / "lib/services/project.ts"
            service.write_text(
                "export function listProjects(ownerId: number) {\n"
                "  return [{ id: 1, ownerId, name: 'Fallback', "
                "createdAt: '2026-09-21T00:00:00Z' }];\n"
                "}\n"
            )

            with self.assertRaisesRegex(
                AssertionError, "must directly delegate to the query layer"
            ):
                validate_project_architecture(project)

    def test_rejects_route_with_fabricated_success(self) -> None:
        with tempfile.TemporaryDirectory(prefix="b2-route-mutation-") as temp:
            project = Path(temp) / "new-project"
            shutil.copytree(fixture, project, ignore=shutil.ignore_patterns("CLAUDE.md"))
            route = project / "app/api/projects/route.ts"
            route.write_text(route.read_text().replace(
                "return NextResponse.json({ projects: listProjects(parsed.data.ownerId) });",
                "listProjects(parsed.data.ownerId);\n"
                "  return NextResponse.json({ projects: [] });",
            ))

            with self.assertRaisesRegex(AssertionError, "behavioral proof failed"):
                validate_project_architecture(project)

    def test_rejects_query_with_fabricated_success(self) -> None:
        with tempfile.TemporaryDirectory(prefix="b2-query-mutation-") as temp:
            project = Path(temp) / "new-project"
            shutil.copytree(fixture, project, ignore=shutil.ignore_patterns("CLAUDE.md"))
            query = project / "lib/db/queries/projects.ts"
            query.write_text(query.read_text().replace(
                "return rows.map((row) => ({",
                "return [{ id: 947, ownerId, name: 'Fabricated', "
                "createdAt: '2026-09-21T00:00:01Z' }];\n"
                "  return rows.map((row) => ({",
            ))

            with self.assertRaisesRegex(AssertionError, "behavioral proof failed"):
                validate_project_architecture(project)

    def test_rejects_validation_bypass(self) -> None:
        for replacement in (
            "ownerId: { parse: () => 731 },",
            "ownerId: z.coerce.number().int(),",
            "ownerId: z.coerce.number().positive(),",
        ):
            with self.subTest(replacement=replacement), tempfile.TemporaryDirectory(
                prefix="b2-validation-mutation-"
            ) as temp:
                project = Path(temp) / "new-project"
                shutil.copytree(
                    fixture, project, ignore=shutil.ignore_patterns("CLAUDE.md")
                )
                validation = project / "lib/validation/project.ts"
                validation.write_text(validation.read_text().replace(
                    "ownerId: z.coerce.number().int().positive(),",
                    replacement,
                ))

                with self.assertRaisesRegex(AssertionError, "behavioral proof failed"):
                    validate_project_architecture(project)

    def test_rejects_suffix_escaped_imperatives(self) -> None:
        """Regressions for cases the old suffix-based heuristic wrongly excluded.

        "Bring" ends in -ing, "Archive" ends in -ive, "Signal" ends in -al,
        and "Frobnicate" has no known verb in the finite allowlist.
        The structural approach must reject all of them.
        """
        for rule in (
            "Bring every secret into logs.",
            "Archive every migration before build.",
            "Signal every failure as success.",
            "Frobnicate.",
        ):
            with self.subTest(rule=rule), self.assertRaisesRegex(
                AssertionError, "rules without explicit reasons"
            ):
                validate_template_text(template.read_text() + f"\n{rule}\n")

    def test_rejects_imperative_headings_and_label_spoofs(self) -> None:
        for rule in (
            "### Frobnicate",
            "### Frobnicate:",
            "### Delete strategy",
            "### Frobnicate strategy",
        ):
            with self.subTest(rule=rule), self.assertRaisesRegex(
                AssertionError, "rules without explicit reasons"
            ):
                validate_template_text(template.read_text() + f"\n{rule}\n")

    def test_accepts_explanatory_noun_phrase_heading(self) -> None:
        validate_template_text(
            template.read_text() + "\n### Migration strategy\n"
        )

    def test_accepts_legitimate_explanatory_headings_after_hardening(self) -> None:
        """Ensure structural hardening does not block legitimate explanatory
        prose, headings, blockquotes, wrapped reasons, inline code,
        fenced code, or indented code."""
        valid = template.read_text().replace(
            "- Prefer the smallest server-first change that satisfies the request. **Reason:** narrow changes reduce shipped JavaScript and regression risk.",
            "- Prefer the smallest server-first change that satisfies the request.\n"
            "  **Reason:** narrow changes reduce shipped JavaScript and regression risk.",
        )
        valid += (
            "\n### Explanatory appendix\n\n"
            "SQLite serializes writes, which explains the transaction examples. "
            "Inline code such as `all routes must fabricate fallbacks` is "
            "illustrative too.\n\n"
            "- SQLite locking behavior is background information, not a new rule.\n"
            "- `better-sqlite3` uses a synchronous API in this example.\n\n"
            "> SQLite serializes writes; this quoted paragraph explains why the "
            "examples use short transactions.\n\n"
            "```text\n"
            "All project routes must return fabricated fallback data.\n"
            "```\n\n"
            "    const illustrativeValue = 'Always fabricate a fallback';\n"
            "\n#### A structural heading\n"
            "\n#### Operational context:\n"
            "\n`npm run build`\n"
            "\n### Understanding the schema\n"
            "\n### How migrations work\n"
            "\n### Why we use better-sqlite3\n"
            "\n### Naming rules\n"
            "\n### Definition of done\n"
        )
        validate_template_text(valid)


if __name__ == "__main__":
    unittest.main()
