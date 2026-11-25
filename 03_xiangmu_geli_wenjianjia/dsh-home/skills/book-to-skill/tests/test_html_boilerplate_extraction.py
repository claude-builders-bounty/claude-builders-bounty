"""extract_html_content() only stripped <script>/<style>/<head> on both the
bs4 and stdlib-fallback paths -- neither does real main-content vs. page-chrome
detection. Verified against 61 real pages scraped from personalmba.com (two
full chapters): a repeated footer block (ad + author bio + copyright notice)
appeared 183 times in the combined extracted text.

trafilatura is purpose-built for "find the article, discard the chrome" and is
now the primary path. This suite covers the fallback contract deterministically
(mocked import/return/exception states) rather than trafilatura's own
boilerplate-detection heuristics, which need realistic page-scale content to
exercise meaningfully and would be flaky against a tiny synthetic fixture --
that behavior is verified against the real 61-page corpus instead (see the PR
description for the before/after numbers).
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from book_to_skill.parsers.html import extract_html_content

SAMPLE_HTML = "<html><body><h1>Chapter 1</h1><p>Real content here.</p></body></html>"


class TestTrafilaturaPrimaryPath:
    def test_uses_trafilatura_result_when_available(self):
        pytest.importorskip("trafilatura")
        with patch("trafilatura.extract", return_value="Chapter 1\nReal content here."):
            result = extract_html_content(SAMPLE_HTML)
        assert result == "Chapter 1\nReal content here."

    def test_falls_back_to_bs4_when_trafilatura_returns_none(self):
        pytest.importorskip("trafilatura")
        with patch("trafilatura.extract", return_value=None):
            result = extract_html_content(SAMPLE_HTML)
        assert "Real content here." in result

    def test_falls_back_to_bs4_when_trafilatura_returns_whitespace_only(self):
        # A near-empty/low-confidence result is still truthy -- must not be
        # returned as-is, or a page trafilatura can't confidently parse
        # silently produces an empty skill instead of falling through.
        pytest.importorskip("trafilatura")
        with patch("trafilatura.extract", return_value="   \n  "):
            result = extract_html_content(SAMPLE_HTML)
        assert "Real content here." in result

    def test_falls_back_to_bs4_when_trafilatura_raises(self):
        # A parse-time exception (e.g. malformed HTML) must not propagate --
        # the whole point of this function is graceful degradation through
        # bs4 -> stdlib, not a hard failure on the best-effort first attempt.
        pytest.importorskip("trafilatura")
        with patch("trafilatura.extract", side_effect=ValueError("simulated parse failure")):
            result = extract_html_content(SAMPLE_HTML)
        assert "Real content here." in result

    def test_falls_back_to_bs4_when_trafilatura_not_installed(self):
        with patch.dict(sys.modules, {"trafilatura": None}):
            result = extract_html_content(SAMPLE_HTML)
        assert "Real content here." in result
