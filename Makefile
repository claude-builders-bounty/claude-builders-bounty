.PHONY: type-check test lint build

type-check:
	python3 -m py_compile hooks/block_destructive_bash.py tests/test_block_destructive_bash.py

test:
	python3 -m unittest discover -s tests -v

lint:
	python3 -m py_compile hooks/block_destructive_bash.py tests/test_block_destructive_bash.py scripts/lint_lines.py
	python3 scripts/lint_lines.py

build:
	python3 -m py_compile hooks/block_destructive_bash.py
