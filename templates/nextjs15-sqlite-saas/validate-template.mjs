import fs from 'node:fs'
import path from 'node:path'

const templatePath = path.join(
  process.cwd(),
  'templates',
  'nextjs15-sqlite-saas',
  'CLAUDE.md'
)

const content = fs.readFileSync(templatePath, 'utf8')

const required = [
  '## Stack And Versions',
  '## Project Structure',
  '## Naming Conventions',
  '## Dev Commands',
  '## SQLite And Migration Conventions',
  '## App Router Patterns',
  '## Component Patterns',
  '## What We Do Not Do',
  '## Claude Behavior In This Repository'
]

const missing = required.filter((heading) => !content.includes(heading))

if (missing.length) {
  console.error('Missing required sections:')
  for (const heading of missing) {
    console.error(`- ${heading}`)
  }
  process.exit(1)
}

if (!content.includes('Reason:')) {
  console.error('Template should explain why rules exist.')
  process.exit(1)
}

console.log('CLAUDE.md template validation passed.')
