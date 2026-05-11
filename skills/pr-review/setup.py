from setuptools import setup

setup(
    name="claude-review",
    version="0.1.0",
    py_modules=["claude_review"],
    entry_points={"console_scripts": ["claude-review=claude_review:main"]},
    python_requires=">=3.9",
)
