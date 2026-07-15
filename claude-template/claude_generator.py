#!/usr/bin/env python3
"""
CLAUDE.md Template Generator for Next.js + SQLite Projects
Bounty: claude-builders-bounty/claude-builders-bounty #2
Author: FanLi (范蠡)
"""

import argparse
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


CLAUDE_MD_TEMPLATE = '''# CLAUDE.md

> Project context for Claude Code - Next.js + SQLite Stack

---

## 🎯 Project Overview

**Name:** {project_name}
**Type:** Next.js Full-Stack Application
**Database:** SQLite (better-sqlite3)
**Created:** {created_date}

### Tech Stack

- **Framework:** Next.js 14+ (App Router)
- **Language:** TypeScript
- **Database:** SQLite via better-sqlite3
- **ORM:** Custom lightweight wrapper
- **Styling:** Tailwind CSS
- **UI Components:** shadcn/ui compatible

---

## 🗂️ Directory Structure

```
{project_name}/
├── app/                    # Next.js App Router
│   ├── api/               # API routes
│   │   └── [route]/
│   │       └── route.ts
│   ├── layout.tsx         # Root layout
│   ├── page.tsx           # Home page
│   ├── globals.css        # Global styles
│   └── ...
├── components/            # React components
│   ├── ui/               # UI components
│   └── ...
├── lib/                   # Utility functions
│   ├── db.ts             # Database connection
│   └── utils.ts          # Helper functions
├── db/                    # Database files
│   ├── schema.sql        # Database schema
│   ├── migrations/       # Migration files
│   └── seed.ts           # Seed data
├── types/                 # TypeScript types
│   └── index.ts
├── public/               # Static assets
├── next.config.js
├── tailwind.config.ts
├── tsconfig.json
└── package.json
```

---

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- npm or pnpm

### Installation

```bash
# Clone and enter project
cd {project_name}

# Install dependencies
npm install

# Setup database
npm run db:init

# Run development server
npm run dev
```

### Database Commands

```bash
# Initialize database
npm run db:init

# Run migrations
npm run db:migrate

# Seed database
npm run db:seed

# Reset database
npm run db:reset
```

---

## 🗄️ Database Architecture

### Connection Pattern

```typescript
// lib/db.ts
import Database from 'better-sqlite3';

const db = new Database('db/app.db');

export function getDb() {{
  return db;
}}

// Use in API routes
import {{ getDb }} from '@/lib/db';

export async function GET() {{
  const db = getDb();
  const users = db.prepare('SELECT * FROM users').all();
  return Response.json({{ users }});
}}
```

### Schema Management

- **Schema file:** `db/schema.sql`
- **Migrations:** `db/migrations/*.sql`
- **Seed data:** `db/seed.ts`

### Common Query Patterns

```typescript
// Single record
const user = db.prepare('SELECT * FROM users WHERE id = ?').get(userId);

// Multiple records
const users = db.prepare('SELECT * FROM users WHERE active = ?').all(1);

// Insert with return
const result = db.prepare(`
  INSERT INTO users (name, email) VALUES (?, ?)
`).run(name, email);

// Update
const result = db.prepare(`
  UPDATE users SET name = ? WHERE id = ?
`).run(name, userId);

// Delete
db.prepare('DELETE FROM users WHERE id = ?').run(userId);
```

---

## 🛠️ Development Guidelines

### When Adding Features

1. **API Routes:** Create in `app/api/[route]/route.ts`
2. **Components:** Place in `components/` with proper naming
3. **Database:**
   - Update `db/schema.sql` for schema changes
   - Create migration in `db/migrations/`
   - Add types to `types/index.ts`

### Code Style

- Use TypeScript strict mode
- Prefer async/await over callbacks
- Use parameterized queries (never string interpolation)
- Handle errors with try/catch
- Use Next.js App Router patterns

### API Route Pattern

```typescript
// app/api/users/route.ts
import {{ NextRequest }} from 'next/server';
import {{ getDb }} from '@/lib/db';

// GET /api/users
export async function GET() {{
  try {{
    const db = getDb();
    const users = db.prepare('SELECT * FROM users').all();
    return Response.json({{ users }});
  }} catch (error) {{
    return Response.json(
      {{ error: 'Failed to fetch users' }},
      {{ status: 500 }}
    );
  }}
}}

// POST /api/users
export async function POST(request: NextRequest) {{
  try {{
    const body = await request.json();
    const db = getDb();

    const result = db.prepare(`
      INSERT INTO users (name, email) VALUES (?, ?)
    `).run(body.name, body.email);

    return Response.json(
      {{ id: result.lastInsertRowid }},
      {{ status: 201 }}
    );
  }} catch (error) {{
    return Response.json(
      {{ error: 'Failed to create user' }},
      {{ status: 500 }}
    );
  }}
}}
```

### Component Pattern

```typescript
// components/UserCard.tsx
interface UserCardProps {{
  user: {{
    id: number;
    name: string;
    email: string;
  }};
}}

export function UserCard({{ user }}: UserCardProps) {{
  return (
    <div className="p-4 border rounded">
      <h3>{{user.name}}</h3>
      <p>{{user.email}}</p>
    </div>
  );
}}
```

---

## 🔧 Configuration Files

### next.config.js

```javascript
/** @type {{import('next').NextConfig}} */
const nextConfig = {{
  experimental: {{
    serverComponentsExternalPackages: ['better-sqlite3']
  }}
}};

module.exports = nextConfig;
```

### Database Configuration

```typescript
// lib/db.ts
import Database from 'better-sqlite3';
import {{ join }} from 'path';

const DB_PATH = process.env.DB_PATH || join(process.cwd(), 'db', 'app.db');

let db: Database.Database | null = null;

export function getDb(): Database.Database {{
  if (!db) {{
    db = new Database(DB_PATH);
    db.pragma('journal_mode = WAL');
  }}
  return db;
}}

export function closeDb() {{
  if (db) {{
    db.close();
    db = null;
  }}
}}
```

---

## 🧪 Testing

### Test Pattern

```typescript
// tests/users.test.ts
import {{ getDb }} from '@/lib/db';

describe('Users API', () => {{
  beforeEach(() => {{
    // Reset and seed test database
  }});

  it('should fetch all users', async () => {{
    // Test implementation
  }});
}});
```

### Run Tests

```bash
# Run all tests
npm test

# Run with coverage
npm run test:coverage

# Run in watch mode
npm run test:watch
```

---

## 📦 Package Scripts

```json
{{
  "scripts": {{
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "db:init": "node scripts/init-db.js",
    "db:migrate": "node scripts/migrate.js",
    "db:seed": "tsx db/seed.ts",
    "db:reset": "rm db/app.db && npm run db:init && npm run db:migrate && npm run db:seed",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage"
  }}
}}
```

---

## 🔒 Security Best Practices

- ✅ Use parameterized queries (prepared statements)
- ✅ Validate all user input with Zod
- ✅ Sanitize data before rendering
- ✅ Use HTTPS in production
- ✅ Store secrets in environment variables
- ✅ Implement proper error handling

### Input Validation Pattern

```typescript
import {{ z }} from 'zod';

const userSchema = z.object({{
  name: z.string().min(1).max(100),
  email: z.string().email(),
}});

export async function POST(request: NextRequest) {{
  const body = await request.json();
  const result = userSchema.safeParse(body);

  if (!result.success) {{
    return Response.json(
      {{ error: 'Invalid input', details: result.error }},
      {{ status: 400 }}
    );
  }}

  // Safe to use result.data
}}
```

---

## 🐛 Common Issues

### Database locked

- Ensure single database instance
- Use WAL mode: `db.pragma('journal_mode = WAL')`
- Close connections properly

### better-sqlite3 build errors

```bash
# Rebuild native modules
npm rebuild better-sqlite3

# Or delete and reinstall
rm -rf node_modules
npm install
```

### Hot reload issues

- SQLite connections persist across reloads
- Use connection pooling or singleton pattern

---

## 📚 Resources

- [Next.js Docs](https://nextjs.org/docs)
- [better-sqlite3 Docs](https://github.com/WiseLibs/better-sqlite3/blob/master/docs/api.md)
- [SQLite Tutorial](https://www.sqlitetutorial.net/)

---

## 🎨 Design System

### Color Palette

- Primary: `{primary_color}`
- Secondary: `{secondary_color}`
- Background: `{bg_color}`
- Text: `{text_color}`

### Typography

- Headings: font-sans, font-bold
- Body: font-sans, font-normal
- Code: font-mono

### Spacing

- Use Tailwind spacing scale: 1, 2, 4, 8, 12, 16, 20, 24...

---

*Generated by CLAUDE.md Template Generator*
*Bounty: claude-builders-bounty/claude-builders-bounty #2 ($75)*
'''


class CLAUDEGenerator:
    """Generator for CLAUDE.md templates"""

    def __init__(self, project_name: str, **kwargs):
        self.project_name = project_name
        self.config = {
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "primary_color": kwargs.get("primary_color", "#0070f3"),
            "secondary_color": kwargs.get("secondary_color", "#7928ca"),
            "bg_color": kwargs.get("bg_color", "#ffffff"),
            "text_color": kwargs.get("text_color", "#000000"),
            **kwargs
        }

    def generate(self) -> str:
        """Generate CLAUDE.md content"""
        return CLAUDE_MD_TEMPLATE.format(
            project_name=self.project_name,
            **self.config
        )

    def generate_package_json(self) -> str:
        """Generate package.json for the project"""
        package = {
            "name": self.project_name.lower().replace(' ', '-'),
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint",
                "db:init": "node scripts/init-db.js",
                "db:migrate": "node scripts/migrate.js",
                "db:seed": "tsx db/seed.ts",
                "db:reset": "rm db/app.db && npm run db:init && npm run db:migrate && npm run db:seed",
                "test": "jest",
                "test:watch": "jest --watch",
                "test:coverage": "jest --coverage"
            },
            "dependencies": {
                "next": "^14.0.0",
                "react": "^18.2.0",
                "react-dom": "^18.2.0",
                "better-sqlite3": "^9.0.0",
                "zod": "^3.22.0",
                "tailwindcss": "^3.3.0",
                "autoprefixer": "^10.4.0",
                "postcss": "^8.4.0"
            },
            "devDependencies": {
                "@types/better-sqlite3": "^7.6.0",
                "@types/node": "^20.0.0",
                "@types/react": "^18.2.0",
                "@types/react-dom": "^18.2.0",
                "eslint": "^8.0.0",
                "eslint-config-next": "^14.0.0",
                "jest": "^29.0.0",
                "ts-node": "^10.9.0",
                "tsx": "^4.0.0",
                "typescript": "^5.0.0"
            }
        }
        return json.dumps(package, indent=2)

    def generate_tsconfig(self) -> str:
        """Generate tsconfig.json"""
        return '''{
  "compilerOptions": {
    "lib": ["dom", "dom.iterable", "esnext"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "bundler",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [{ "name": "next" }],
    "paths": { "@/*": ["./*"] }
  },
  "include": ["next-env.d.ts", "**/*.ts", "**/*.tsx", ".next/types/**/*.ts"],
  "exclude": ["node_modules"]
}'''

    def generate_next_config(self) -> str:
        """Generate next.config.js"""
        return '''/** @type {import('next').NextConfig} */
const nextConfig = {
  experimental: {
    serverComponentsExternalPackages: ['better-sqlite3']
  }
};

module.exports = nextConfig;'''

    def generate_tailwind_config(self) -> str:
        """Generate tailwind.config.ts"""
        return f'''import type {{ Config }} from 'tailwindcss';

const config: Config = {{
  content: [
    './pages/**/*.{{js,ts,jsx,tsx,mdx}}',
    './components/**/*.{{js,ts,jsx,tsx,mdx}}',
    './app/**/*.{{js,ts,jsx,tsx,mdx}}',
  ],
  theme: {{
    extend: {{
      colors: {{
        primary: '{self.config["primary_color"]}',
        secondary: '{self.config["secondary_color"]}',
      }},
    }},
  }},
  plugins: [],
}};

export default config;'''

    def generate_db_utils(self) -> str:
        """Generate database utilities"""
        return '''import Database from 'better-sqlite3';
import { join } from 'path';

const DB_PATH = process.env.DB_PATH || join(process.cwd(), 'db', 'app.db');

let db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!db) {
    db = new Database(DB_PATH);
    db.pragma('journal_mode = WAL');
  }
  return db;
}

export function closeDb(): void {
  if (db) {
    db.close();
    db = null;
  }
}

export function initDb(): void {
  const db = getDb();
  // Run schema initialization
  // db.exec(...)
}
'''

    def generate_all_files(self) -> Dict[str, str]:
        """Generate all project files"""
        return {
            "CLAUDE.md": self.generate(),
            "package.json": self.generate_package_json(),
            "tsconfig.json": self.generate_tsconfig(),
            "next.config.js": self.generate_next_config(),
            "tailwind.config.ts": self.generate_tailwind_config(),
            "lib/db.ts": self.generate_db_utils(),
        }


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Generate CLAUDE.md template for Next.js + SQLite projects"
    )
    parser.add_argument(
        "project_name",
        help="Name of the project"
    )
    parser.add_argument(
        "--output", "-o",
        default=".",
        help="Output directory (default: current directory)"
    )
    parser.add_argument(
        "--primary-color",
        default="#0070f3",
        help="Primary color (default: #0070f3)"
    )
    parser.add_argument(
        "--secondary-color",
        default="#7928ca",
        help="Secondary color (default: #7928ca)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print files without writing"
    )

    args = parser.parse_args()

    generator = CLAUDEGenerator(
        project_name=args.project_name,
        primary_color=args.primary_color,
        secondary_color=args.secondary_color
    )

    files = generator.generate_all_files()
    output_dir = Path(args.output)

    if args.dry_run:
        print("Files to be generated:")
        print("=" * 60)
        for filepath, content in files.items():
            print(f"\n📄 {filepath}")
            print("-" * 60)
            print(content[:500] + "..." if len(content) > 500 else content)
        return

    # Write files
    for filepath, content in files.items():
        full_path = output_dir / filepath
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content, encoding='utf-8')
        print(f"✅ Created: {full_path}")

    print(f"\n🎉 Generated CLAUDE.md template for '{args.project_name}'")
    print(f"📁 Output directory: {output_dir.absolute()}")
    print("\nNext steps:")
    print(f"  cd {output_dir}")
    print("  npm install")
    print("  npm run db:init")
    print("  npm run dev")


if __name__ == "__main__":
    main()
