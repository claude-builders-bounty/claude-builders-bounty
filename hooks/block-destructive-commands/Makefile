.PHONY: test ci-validate

test:
	python3 -m unittest discover -s tests -v

ci-validate:
	bash tests/run-ci-checks.sh
