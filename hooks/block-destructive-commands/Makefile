.PHONY: test ci-validate

test:
	python3 -m unittest discover -s tests -v

ci-validate: test
	git diff --check
	@if grep -rE 'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor' \
		pre-tool-use.py install.sh README.md settings.json tests/; then \
		echo 'Forbidden agent attribution strings found in hook sources'; \
		exit 1; \
	fi
	@if git -C ../.. log -1 --format=%B | grep -qiE 'cursoragent@cursor\.com|Made with Cursor|Co-authored-by: Cursor'; then \
		echo 'Forbidden agent attribution strings found in latest commit message'; \
		exit 1; \
	fi
