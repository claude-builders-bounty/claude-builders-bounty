#!/usr/bin/env python3
"""
MCP Server: Bounty Automation Tools
Integrates all bounty tools as MCP tools for Claude Code
"""

import asyncio
import json
from mcp.server import Server
from mcp.types import Tool, TextContent
import subprocess
import sys
from pathlib import Path

# Create MCP server
server = Server("bounty-automation")


@server.tool()
async def review_pr(base_branch: str = "main") -> str:
    """
    Review pull requests for security, bugs, performance, and style issues.

    Args:
        base_branch: Branch to compare against (default: main)

    Returns:
        Structured Markdown report with findings
    """
    try:
        result = subprocess.run(
            [sys.executable, "pr-reviewer/pr_reviewer.py", "--base", base_branch],
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.stdout
    except Exception as e:
        return f"Error running PR review: {str(e)}"


@server.tool()
async def generate_changelog(since_tag: str = None) -> str:
    """
    Generate CHANGELOG.md from git commit history.

    Args:
        since_tag: Tag to start from (auto-detected if not provided)

    Returns:
        Generated CHANGELOG content
    """
    try:
        result = subprocess.run(
            [sys.executable, "changelog_generator.py"],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Read generated CHANGELOG
        changelog_path = Path("CHANGELOG.md")
        if changelog_path.exists():
            return changelog_path.read_text()
        return result.stdout
    except Exception as e:
        return f"Error generating changelog: {str(e)}"


@server.tool()
async def generate_claude_template(project_name: str, output_dir: str = ".") -> str:
    """
    Generate CLAUDE.md template for Next.js + SQLite projects.

    Args:
        project_name: Name of the project
        output_dir: Output directory (default: current directory)

    Returns:
        Path to generated files
    """
    try:
        result = subprocess.run(
            [
                sys.executable,
                "claude-template/claude_generator.py",
                project_name,
                "--output", output_dir
            ],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout
    except Exception as e:
        return f"Error generating CLAUDE.md template: {str(e)}"


@server.tool()
async def check_command_safety(command: str) -> dict:
    """
    Check if a bash command is safe to execute.

    Args:
        command: Command to check

    Returns:
        Dictionary with allow status and reason
    """
    try:
        result = subprocess.run(
            [sys.executable, "block_hook.py", command],
            capture_output=True,
            text=True,
            timeout=10
        )
        return json.loads(result.stdout)
    except Exception as e:
        return {"allow": False, "message": f"Error checking command: {str(e)}"}


@server.resource("bounty://tools")
async def get_available_tools() -> str:
    """List all available bounty automation tools"""
    tools = {
        "review_pr": "Review pull requests for security, bugs, performance, style",
        "generate_changelog": "Generate CHANGELOG.md from git history",
        "generate_claude_template": "Generate CLAUDE.md for Next.js + SQLite projects",
        "check_command_safety": "Check if bash command is safe to execute"
    }
    return json.dumps(tools, indent=2)


async def main():
    """Run MCP server"""
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
