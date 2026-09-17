import { test } from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import Database from 'better-sqlite3';
import { migrate } from '../scripts/migrate.mjs';
function fixture(t) { const dir=fs.mkdtempSync(path.join(os.tmpdir(),'migration-fixture-'));const db=new Database(':memory:');t.after(()=>{db.close();fs.rmSync(dir,{recursive:true});});return {dir,db,write:(name,sql)=>fs.writeFileSync(path.join(dir,name),sql)}; }
test('fresh database and repeated migration',t=>{const f=fixture(t);f.write('0001_initial.sql','CREATE TABLE example (id INTEGER PRIMARY KEY);');assert.equal(migrate(f.db,f.dir),1);assert.equal(migrate(f.db,f.dir),0);assert.equal(f.db.prepare('SELECT COUNT(*) AS n FROM schema_migrations').get().n,1);});
test('changed applied migration is refused',t=>{const f=fixture(t);f.write('0001_initial.sql','CREATE TABLE example (id INTEGER);');migrate(f.db,f.dir);f.write('0001_initial.sql','CREATE TABLE changed (id INTEGER);');assert.throws(()=>migrate(f.db,f.dir),/changed/);});
test('failed migration rolls back the entire pending batch',t=>{const f=fixture(t);f.write('0001_initial.sql','CREATE TABLE example (id INTEGER);');f.write('0002_broken.sql','NOT VALID SQL;');assert.throws(()=>migrate(f.db,f.dir));assert.equal(f.db.prepare("SELECT COUNT(*) AS n FROM sqlite_master WHERE name='example'").get().n,0);});
test('duplicate versions rejected',t=>{const f=fixture(t);f.write('0001_first.sql','SELECT 1;');f.write('0001_second.sql','SELECT 2;');assert.throws(()=>migrate(f.db,f.dir),/Duplicate/);});
test('upgrade preserves existing rows',t=>{const f=fixture(t);f.write('0001_initial.sql','CREATE TABLE example (id INTEGER PRIMARY KEY, name TEXT NOT NULL);');migrate(f.db,f.dir);f.db.prepare('INSERT INTO example VALUES (?, ?)').run(1,'retained');f.write('0002_add_column.sql','ALTER TABLE example ADD COLUMN active INTEGER NOT NULL DEFAULT 1;');assert.equal(migrate(f.db,f.dir),1);assert.deepEqual(f.db.prepare('SELECT * FROM example').get(),{id:1,name:'retained',active:1});});
test('deleted migration is refused',t=>{const f=fixture(t);f.write('0001_initial.sql','SELECT 1;');migrate(f.db,f.dir);fs.unlinkSync(path.join(f.dir,'0001_initial.sql'));assert.throws(()=>migrate(f.db,f.dir),/disappeared/);});
test('out of order migration is refused',t=>{const f=fixture(t);f.write('0002_second.sql','SELECT 2;');migrate(f.db,f.dir);f.write('0001_first.sql','SELECT 1;');assert.throws(()=>migrate(f.db,f.dir),/Out-of-order/);});
