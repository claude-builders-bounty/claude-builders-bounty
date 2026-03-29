from setuptools import setup, find_packages

setup(
    name="safety-hook",
    version="1.0.0",
    description="Pre-tool-use safety hook for Claude Code",
    author="Claude Builders Bounty",
    py_modules=["safety_hook"],
    install_requires=[
        # No external dependencies - uses only stdlib
    ],
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
