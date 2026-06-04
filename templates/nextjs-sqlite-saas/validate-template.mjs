import { readFile } from "node:fs/promises";

const text = await readFile(new URL("./CLAUDE.md", import.meta.url), "utf8");

const required = [
  "Next.js 15",
  "SQLite",
  "Folder Structure",
  "Naming Conventions",
  "SQL & Migration Conventions",
  "Component Patterns",
  "Dev Commands",
  "What We Do Not Do",
  "Reason:"
];

const missing = required.filter((item) => !text.includes(item));
if (missing.length) {
  console.error(JSON.stringify({ ok: false, missing }, null, 2));
  process.exit(1);
}

const reasonCount = (text.match(/Reason:/g) || []).length;
const commandCount = (text.match(/npm run/g) || []).length;

console.log(
  JSON.stringify(
    {
      ok: true,
      required_sections_present: required.length,
      reason_count: reasonCount,
      npm_command_count: commandCount,
      usable_as_root_claude_md: true
    },
    null,
    2
  )
);
