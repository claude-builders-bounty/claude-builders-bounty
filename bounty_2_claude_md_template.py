#!/usr/bin/env python3
"""
Bounty #2: CLAUDE.md Template for Next.js + SQLite SaaS
Generates a CLAUDE.md file with setup instructions for a Next.js + SQLite SaaS project.
"""

import argparse
import os


def generate_claude_md(
    project_name="my-saas",
    description="A SaaS application built with Next.js and SQLite",
    tech_stack=["nextjs", "sqlite", "python", "supabase"],
    features=["auth", "payments", "api", "webhook"],
    install_commands=None,
):
    """
    Generate a CLAUDE.md file content for a Next.js + SQLite SaaS project.
    
    The CLAUDE.md file provides Claude Code with context about the project
    so it can provide better assistance.
    """
    if install_commands is None:
        install_commands = {
            "python": "pip install -r requirements.txt",
            "nextjs": "npm install && npm run build",
            "sqlite": "No install needed - built into Python",
        }
    
    lines = []
    
    # Project header
    lines.append(f"# {project_name}")
    lines.append("")
    lines.append(f"> {description}")
    lines.append("")
    
    # Technology stack
    lines.append("## Technology Stack")
    lines.append("")
    lines.append("- **Frontend**: Next.js 14 (App Router)")
    lines.append("- **Database**: SQLite with SQLAlchemy ORM")
    lines.append("- **Backend**: Python + FastAPI")
    lines.append("- **Deployment**: Vercel + Railway")
    lines.append("- **Authentication**: NextAuth.js / Auth0")
    lines.append("- **Payments**: Stripe integration")
    lines.append("")
    
    # Project setup
    lines.append("## Project Setup")
    lines.append("")
    
    # Prerequisites
    lines.append("### Prerequisites")
    lines.append("")
    lines.append("```bash")
    lines.append("# Install Node.js dependencies")
    lines.append("npm install")
    lines.append("")
    lines.append("# Install Python dependencies")
    lines.append("pip install -r requirements.txt")
    lines.append("```")
    lines.append("")
    
    # Environment setup
    lines.append("### Environment Variables")
    lines.append("")
    lines.append("# Create .env file")
    lines.append("cp .env.example .env")
    lines.append("")
    lines.append("# Edit .env with your values")
    lines.append("# NEXT_PUBLIC_STORE_ID=your_stripe_store_id")
    lines.append("# DATABASE_URL=file://./dev.db")
    lines.append("# NEXTAUTH_URL=http://localhost:3000")
    lines.append("# STRIPE_SECRET_KEY=your_stripe_secret")
    lines.append("")
    
    # Development commands
    lines.append("### Development")
    lines.append("")
    lines.append("```bash")
    lines.append("# Start Next.js dev server")
    lines.append("npm run dev")
    lines.append("")
    lines.append("# Start Python/FastAPI server")
    lines.append("uvicorn app.main:app --reload")
    lines.append("```")
    lines.append("")
    
    # Database migrations
    lines.append("### Database")
    lines.append("")
    lines.append("```bash")
    lines.append("# Create SQLite database")
    lines.append("python init_db.py")
    lines.append("")
    lines.append("# Run migrations")
    lines.append("python manage.py db migrate")
    lines.append("```")
    lines.append("")
    
    # Project structure
    lines.append("## Project Structure")
    lines.append("")
    lines.append("```")
    lines.append("src/")
    lines.append("  ├── app/           # Next.js app router pages")
    lines.append("  ├── api/           # API routes (FastAPI)")
    lines.append("  ├── components/    # React components")
    lines.append("  ├── lib/           # Utility libraries")
    lines.append("  └── styles/        # CSS/SCSS styles")
    lines.append("scripts/")
    lines.append("  ├── init_db.py     # Database initialization")
    lines.append("  └── migrations/    # DB migration scripts")
    lines.append("tests/")
    lines.append("  ├── unit/          # Unit tests")
    lines.append("  └── integration/   # Integration tests")
    lines.append("```")
    lines.append("")
    
    # Code style
    lines.append("## Code Style")
    lines.append("")
    lines.append("- Follow Prettier formatting (npm run format)")
    lines.append("- Use TypeScript for Next.js components")
    lines.append("- Follow PEP 8 for Python code")
    lines.append("- Conventional Commits for git messages")
    lines.append("- Use black for Python formatting")
    lines.append("- Use eslint for JS/TS linting")
    lines.append("")
    
    # Common tasks
    lines.append("## Common Tasks")
    lines.append("")
    
    # Deployment
    lines.append("### Deployment to Vercel")
    lines.append("")
    lines.append("```bash")
    lines.append("vercel")
    lines.append("vercel --prod")
    lines.append("```")
    lines.append("")
    
    # Testing
    lines.append("### Testing")
    lines.append("")
    lines.append("```bash")
    lines.append("# Run unit tests")
    lines.append("pytest tests/ -v")
    lines.append("")
    lines.append("# Run integration tests")
    lines.append("pytest tests/integration/ -v")
    lines.append("```")
    lines.append("")
    
    # Linting
    lines.append("### Linting")
    lines.append("")
    lines.append("```bash")
    lines.append("# Check formatting")
    lines.append("npm run format -- --check")
    lines.append("")
    lines.append("# Lint Python")
    lines.append("black --check .")
    lines.append("")
    lines.append("# Lint JS/TS")
    lines.append("eslint .")
    lines.append("```")
    lines.append("")
    
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Generate CLAUDE.md template for Next.js + SQLite SaaS"
    )
    parser.add_argument(
        "--project-name",
        default="my-saas",
        help="Project name (default: my-saas)",
    )
    parser.add_argument(
        "--description",
        default="A SaaS application built with Next.js and SQLite",
        help="Project description",
    )
    parser.add_argument(
        "--output",
        default="CLAUDE.md",
        help="Output file path (default: CLAUDE.md)",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="Skip project header",
    )
    
    args = parser.parse_args()
    
    content = generate_claude_md(
        project_name=args.project_name,
        description=args.description,
    )
    
    with open(args.output, "w", encoding="utf-8") as f:
        f.write(content)
    
    print(f"CLAUDE.md generated: {args.output}")
    print(f"File size: {len(content)} bytes")


if __name__ == "__main__":
    main()