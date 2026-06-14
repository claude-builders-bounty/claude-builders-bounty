from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "CLAUDE.md"

REQUIRED_SECTIONS = (
    "## Stack And Versions",
    "## Folder Structure",
    "## SQL And Migration Conventions",
    "## Auth, Tenancy, And Caching",
    "## Component Patterns",
    "## Dev Commands",
    "## Anti-Patterns To Avoid",
)

REQUIRED_GUARDRAILS = (
    "not compatible with the Edge runtime",
    "hosted multi-instance or serverless deployments",
    "organization_id",
    "revalidatePath",
    "rollback",
    "Do not put database calls in Client Components",
)


def main() -> None:
    text = TEMPLATE.read_text(encoding="utf-8")
    missing_sections = [item for item in REQUIRED_SECTIONS if item not in text]
    missing_guardrails = [item for item in REQUIRED_GUARDRAILS if item not in text]
    reasons = text.count("Reason:")

    assert not missing_sections, f"Missing sections: {missing_sections}"
    assert not missing_guardrails, f"Missing guardrails: {missing_guardrails}"
    assert reasons >= 10, f"Expected at least 10 rationale blocks, found {reasons}"
    print("CLAUDE.md template validation passed")


if __name__ == "__main__":
    main()
