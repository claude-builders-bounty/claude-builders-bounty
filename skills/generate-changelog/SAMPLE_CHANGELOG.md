# Changelog — zod

All notable changes to this project are documented in this file.

## [Unreleased (since v4.6.7)] - 2026-11-21

### Added
- list security@zod.dev and add a security.txt (#6736) (`a6b6263`)
- add zod-i18n-map, Mimlet and zod-india (#6730) (`93b7a62`)
- add MongoZod to Powered by Zod (#6727) (`77e72ec`)
- add Sizable.map to es, fr, he, hr and lt, and check Sizable parity from source (#6661) (`40a5dba`)

### Fixed
- let z.intersection merge cyclic outputs instead of overflowing (#6764) (`2a343ed`)
- stop shared nodes from doubling the issue count per level (#6763) (`41e286c`)
- skip a record key that converts to __proto__ at the write (#6760) (`90bf57b`)
- hand an intersection's rejection back to the runtime in compiled code (#6762) (`c5ce5f6`)
- resolve the whole JSON Pointer in a fromJSONSchema $ref (#6761) (`00f532f`)
- list null in nullable enums in openapi-3.0 output (#6759) (`1e09924`)
- omit internal format names for includes/startsWith/endsWith in toJSONSchema (#6756) (`fef16cb`)
- remove literal "undefined" from lt and hy messages (#6755) (`4fb18a3`)
- emit valid JSON Schema for empty tuples (#6754) (`b539e16`)
- copy a path a transform pushes before any receiver prefixes it (#6739) (`19c40d2`)
- re-run a z.lazy getter that threw instead of answering undefined (#6688) (#6740) (`6fd0477`)
- wait on a node a concurrent async visit still holds (#6738) (`2ec830f`)
- report a capped union option on encode (#6735) (`ab1e132`)
- skip a shape key that has no descriptor (#6684) (#6734) (`cc96d77`)
- stop Rollup warning about annotation tokens in comments (#6729) (`2720b8a`)
- fix wrong API names, Mini examples and the Error note (#6728) (`30d0f9f`)
- prefix issue paths in place in the object JIT (#6710) (`2554b70`)
- run nested checks when encoding a recursive schema (#6707) (`b1f6ba0`)
- match z.templateLiteral with string parts in linear time (#6706) (`3a20805`)
- stop the memoizer copying every issue below each recursive node (#6705) (`1bd44af`)
- forward a child's issues without spreading them into push() (#6701) (`c504186`)
- check a size bound placed after a refinement, and on encode (#6698) (`7989d07`)
- reconcile intersection keys in linear time (#6697) (`a4a049b`)
- check array and set size bounds before parsing elements (#6696) (`c987c29`)
- write each async tuple rest element to its own index (#6702) (`586813a`)
- report a union option that only checks rejected (#6662) (`680d19f`)

### Changed
- generate sitemap.xml from the docs and blog sources, and point robots.txt at it (`e32e088`)
- pin chrome-devtools-mcp and launch it on chrome-headless-shell (#6733) (`8651451`)
- provision Node from .nvmrc instead of latest (#6725) (`e43ed93`)
- count intersection key scans instead of timing them (#6704) (`33494f3`)
- say .validate() stops at the first failure, on Basics and the AOT page (#6703) (`7916d60`)
- the approval summary tells the maintainer to run stager, not stager approve (#6675) (`afdac65`)
- only the approved release job can create a tag, and the dispatch carries the notes (#6672) (`f1ffdf5`)

### Removed
- tag before installing dependencies, and delete the key after the push (#6674) (`a66e698`)
