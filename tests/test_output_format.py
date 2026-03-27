from claude_review import ensure_structure


def test_output_format_sections_present():
    text = """## Summary\nTest\n\n## Risks\n- one\n\n## Suggestions\n- two\n\n## Confidence\nHigh\n"""
    out = ensure_structure(text)
    assert "## Summary" in out
    assert "## Risks" in out
    assert "## Suggestions" in out
    assert "## Confidence" in out
