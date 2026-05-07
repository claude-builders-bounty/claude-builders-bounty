# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).


## [v1.0.0-demo] - 2026-05-07

### Added
- Add R16 Exhibition Planning project scaffold (bc85b27)
- Notion-ops v2.0: migrate from MCP to notion-cli + add setup.md (f0e9b2e)
- Add R17 Brainstorming project scaffold (d046c1a)
- Add O37 HTML Report Ops project scaffold (e7dc776)
- Add html-report-deploy skill (Surge.sh backend) (a57cf10)
- Github-deploy v1.1: add pull/sync verification workflow (4f59a2d)
- Sync project work + new skills (1979bdd)
- SETUP.md: add Surfagent + Telegram bot setup steps (ab0d1c5)

### Changed
- EU price axis editable slide + PNG screenshot (07ab102)
- Cross-project updates (7bd5759)

### Fixed
- V2: model fallback, Hebrew detection, RTL font fix, improved prompts (82096a4)
- Use single-run translation to prevent stretched text in justified paragraphs (0325ef9)
- Translate VML text boxes + text boxes in headers/footers (bd68c43)
- Add 3x retry logic for failed API calls to prevent untranslated paragraphs (e4c1371)
- Preserve full rPr XML for fonts, enable text box auto-shrink for all languages (3c9092a)
- Poll-bot docs: cross-link --resolve to Slack token from Step 9a (7590975)

### Other
- Slides-ops v1.5: layout-driven sizing, flush-left default, no padding compensation (17b4aaf)
- Sync local work + ignore R02 fp400 transient payloads (2074153)
- Gws-run: agent identity (service-account) mode (8e020f6)
- Gws-run agent mode: strip stale CREDENTIALS_FILE, use group access (8fc36f5)
- Gws agent identity: consolidate docs into setup.md, slim SKILL.md (63f41e7)
- Slides-ops v1.6: tables — uniform sizing, no flush-left in cells, MIDDLE align (cc11b33)
- Locations skill v1.3: NPR/OMP, PLT, Notion Trackers, Proxy folder (fd244fc)
- R18 Other Reports: split ad-hoc Notion reports out of R02 (2418b14)
- SETUP.md: explain how to get the Notion integration token (3516fe5)
- AGENT_RULES.md: document ~/.claude/skills junction for CC auto-load (a698330)
- Consolidate browser-use to Surfagent; harden agent Chrome rules (0ea0361)
