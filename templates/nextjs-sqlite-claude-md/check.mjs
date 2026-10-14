#!/usr/bin/env node
/**
 * Validates that CLAUDE.md and the fixture project agree.
 *
 * A CLAUDE.md is only "usable without modification" if the commands and paths it
 * documents actually exist. This script fails when the document drifts from the
 * project, which is the failure mode of every hand-written CLAUDE.md.
 *
 * Usage: node check.mjs [CLAUDE.md] [fixture-dir]
 */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const here = path.dirname(fileURLToPath(import.meta.url));
const claudePath = path.resolve(process.argv[2] ?? path.join(here, 'CLAUDE.md'));
const fixtureDir = path.resolve(process.argv[3] ?? path.join(here, 'fixture'));

const md = fs.readFileSync(claudePath, 'utf8');
const pkg = JSON.parse(fs.readFileSync(path.join(fixtureDir, 'package.json'), 'utf8'));
const scripts = new Set(Object.keys(pkg.scripts ?? {}));
const envExample = fs.readFileSync(path.join(fixtureDir, '.env.example'), 'utf8');

let pass = 0;
const failures = [];
const ok = (msg) => { pass += 1; console.log(`  ok    ${msg}`); };
const bad = (msg) => { failures.push(msg); console.log(`  FAIL  ${msg}`); };

console.log(`CLAUDE.md: ${path.relative(process.cwd(), claudePath)}`);
console.log(`fixture:   ${path.relative(process.cwd(), fixtureDir)}`);

// 1. Sections the bounty asks for.
console.log('\nsecciones obligatorias');
const secciones = [
  ['stack y versiones', /^##\s+Stack and versions/im],
  ['estructura de carpetas', /^##\s+Folder structure/im],
  ['comandos de desarrollo', /^##\s+Dev commands/im],
  ['convenciones SQL / migraciones', /^##\s+SQL and migration conventions/im],
  ['patrones de componentes', /^##\s+Component patterns/im],
  ['lo que no hacemos', /^##\s+What we don't do/im],
];
for (const [nombre, re] of secciones) {
  if (re.test(md)) ok(`seccion presente: ${nombre}`);
  else bad(`falta la seccion: ${nombre}`);
}

// 2. Every `npm run <script>` mentioned must exist in package.json.
console.log('\ncomandos npm documentados');
const runs = [...new Set([...md.matchAll(/npm run ([a-zA-Z0-9:_-]+)/g)].map((m) => m[1]))];
if (runs.length < 6) bad(`solo se documentan ${runs.length} comandos, parece incompleto`);
for (const script of runs) {
  if (scripts.has(script)) ok(`npm run ${script} existe en package.json`);
  else bad(`npm run ${script} esta documentado pero NO existe en package.json`);
}

// 3. Concrete file paths mentioned must exist in the fixture (a bare filename is
//    resolved by unique basename, so conventions like `loading.tsx` still count).
console.log('\nrutas citadas');
const ilustrativa = (p) => /[<*]/.test(p) || /^\d{4}_/.test(p);

function resolver(ruta) {
  const directo = path.join(fixtureDir, ruta);
  if (fs.existsSync(directo)) return directo;
  if (ruta.includes('/')) return null;
  const encontrados = [];
  const recorrer = (dir) => {
    for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
      if (entry.name === 'node_modules' || entry.name === '.next' || entry.name === 'data') continue;
      const full = path.join(dir, entry.name);
      if (entry.isDirectory()) recorrer(full);
      else if (entry.name === ruta) encontrados.push(full);
    }
  };
  recorrer(fixtureDir);
  return encontrados.length === 1 ? encontrados[0] : null;
}

const rutas = [...new Set([...md.matchAll(/`([a-zA-Z0-9._/-]+\.(?:ts|tsx|sql|mjs|json))`/g)].map((m) => m[1]))];
let verificadas = 0;
for (const ruta of rutas) {
  if (ilustrativa(ruta)) continue;
  verificadas += 1;
  const encontrado = resolver(ruta);
  if (encontrado) ok(`existe: ${ruta}`);
  else bad(`se cita ${ruta} y no existe en el proyecto`);
}
if (verificadas < 5) bad(`solo se pudieron verificar ${verificadas} rutas concretas; el check seria vacio`);

// 4. Environment variables documented must be in .env.example.
console.log('\nvariables de entorno');
const bloque = md.match(/^##\s+Environment[\s\S]*$/im)?.[0] ?? '';
const vars = [...new Set([...bloque.matchAll(/^\s*([A-Z][A-Z0-9_]+)=/gm)].map((m) => m[1]))];
for (const v of vars) {
  if (envExample.includes(`${v}=`)) ok(`${v} esta en .env.example`);
  else bad(`${v} se documenta y no aparece en .env.example`);
}

console.log(`\nRESULTADO: ${pass} comprobaciones ok, ${failures.length} fallos`);
if (failures.length) {
  console.log('\nFallos:');
  for (const f of failures) console.log(` - ${f}`);
  process.exit(1);
}
