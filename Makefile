.PHONY: test
test:
	python3 -m unittest discover -s pr-reviewer/tests -v
