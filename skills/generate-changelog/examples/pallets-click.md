# Changelog

> Reproducible sample generated from https://github.com/pallets/click
> Base tag: `8.4.2` · Pinned HEAD: `b67832c2167e5b0ff6764a8c04a0a9087e697b5a`
> Command: `bash changelog.sh --repo click --output examples/pallets-click.md --version Unreleased`

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-07-09

### Added

- Add help parameter to arguments (`684b3f5`)
- Add \`@custom_version_option\`, freeze \`@version_option\` (`9f9b149`)
- Add format_filename and sentinel files. (`18400b2`)
- Add KeepOpenFile, LazyFile and open_file files. (`7007982`)
- Add files for _detect_program_name, _expand_args, and make_default_short_help. (`47cc96f`)

### Fixed

- Fix dev version in 8.4.1 (`37aa0c6`)
- Fix broken fish completion and multiline help string (`c353590`)

### Changed

- start version 8.5.0 (`4e869f3`)
- Move changes to markdown (`03d3b8a`)
- optimize split_arg_string with extend(...) instead of a for loop system. (`748a34d`)
- type-hint out varibale (`c4a6b57`)
- Do not trigger a \`BytesWarning\` under \`python -bb\` (`6f85d26`)
- Strip ANSI from \`confirm()\` and \`prompt()\` when the stream don't support them (`93ba007`)
- Don't parameterize tests using non-Collection iterables (`30749b4`)
- Use \`click.echo\` everywhere in the docs, document exception (`4453103`)
- Update documentation following Colorama removal (`13f075c`)
- Make test echo file. (`a391797`)
- Make confirm, prompt, style files. (`182944f`)
- Move move test to prompt file. (`1103c5c`)
- Restore \`test_echo_color_flag\` from #3505 that was lost in #3674 merge (`c52f43c`)
- Validate style() color arguments, fix explicit black color argument (`07c909f`)
- Warn when an argument name collide with other parameters (`3495fba`)
- Strip all ANSI sequences (`71f2baf`)

### Removed

- remove colorama (`7454647`)

<!-- Generated from 8.4.2..HEAD; 24 commit(s). -->
