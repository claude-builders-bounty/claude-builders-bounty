.PHONY: test test-bash test-python clean

test: test-bash test-python

test-bash:
	@bash generate_changelog.sh /tmp/test-changelog.md . && echo "✅ Bash: OK"

test-python:
	@python3 generate_changelog.py /tmp/test-changelog.md . && echo "✅ Python: OK"

clean:
	rm -f /tmp/test-changelog.md
