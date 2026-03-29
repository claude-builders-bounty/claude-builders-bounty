from setuptools import setup, find_packages

setup(
    name="dangerous-command-guard",
    version="1.0.0",
    description="Claude Code pre-tool-use hook that blocks destructive bash commands",
    py_modules=["dangerous_command_guard"],
    package_dir={"": "hooks/pre-tool-use"},
    entry_points={
        "console_scripts": [
            "dangerous-command-guard=dangerous_command_guard:main",
        ]
    },
    python_requires=">=3.8",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
