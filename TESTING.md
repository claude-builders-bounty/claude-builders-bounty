# Testing

## Run Tests

```bash
python3 tests.py
```

## What's Tested

- File exists at repo root
- Line count under 500
- Required sections present (Stack, Structure, Migrations, Components, Anti-patterns)
- SQLite pragmas documented
- Zod validation patterns included
- "Why" explanations present (not just rules)
- Markdown lint (trailing whitespace)

## Expected Output

```
✅ test_file_exists
✅ test_line_count
✅ test_has_stack_section
✅ test_has_folder_structure
✅ test_has_migration_conventions
✅ test_has_component_patterns
✅ test_has_anti_patterns
✅ test_has_dev_commands
✅ test_has_why_explanations
✅ test_has_sqlite_pragmas
✅ test_has_zod_validation
✅ test_no_markdown_lint_errors

==================================================
Results: 12 passed, 0 failed out of 12
```
