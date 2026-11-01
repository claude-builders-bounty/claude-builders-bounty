"""claude-review: structured PR reviews for Claude Code."""


def _entry():
    from claude_review.cli import main
    raise SystemExit(main())


if __name__ == "__main__":
    _entry()
