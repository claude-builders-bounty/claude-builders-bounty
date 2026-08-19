<!--
Verbatim output of changelog.sh — nothing below was edited by hand.

Repository: https://github.com/anthropics/anthropic-sdk-python (at v0.122.0, ad53cac8)

Commands:
  ./changelog.sh --to v0.121.0 --output CHANGELOG.md   # older release first
  ./changelog.sh --output CHANGELOG.md                 # newest release on top
-->

# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v0.122.0] - 2026-08-13

> 28 commits since `v0.121.0` · [full diff](https://github.com/anthropics/anthropic-sdk-python/compare/v0.121.0...v0.122.0)

### Added

- **api**: add output_behavior to dream creation (create a new memory store or update the input store in place) ([`1571dddf`](https://github.com/anthropics/anthropic-sdk-python/commit/1571dddf))

### Changed

- use the not_given singleton instead of the legacy NOT_GIVEN alias ([`db4581da`](https://github.com/anthropics/anthropic-sdk-python/commit/db4581da))
- codegen metadata ([`f1c1701f`](https://github.com/anthropics/anthropic-sdk-python/commit/f1c1701f))

### Fixed

- **client**: keep token exchange bound per client across copy() ([#388](https://github.com/anthropics/anthropic-sdk-python/pull/388))
- **streaming**: keep omitted content block fields unset in accumulated messages ([#346](https://github.com/anthropics/anthropic-sdk-python/pull/346))
- **client**: read PathLike contents passed inside a file tuple ([`934d4296`](https://github.com/anthropics/anthropic-sdk-python/commit/934d4296))
- **streaming**: apply all message_delta fields when accumulating streamed messages ([#380](https://github.com/anthropics/anthropic-sdk-python/pull/380))
- **streaming**: run the request transform once in messages.stream() ([#347](https://github.com/anthropics/anthropic-sdk-python/pull/347))
- **bedrock,aws**: run SigV4 signing off the event loop in async clients ([#334](https://github.com/anthropics/anthropic-sdk-python/pull/334))
- **streaming**: add context to malformed tool input JSON errors in the non-beta accumulator ([#339](https://github.com/anthropics/anthropic-sdk-python/pull/339))
- **streaming**: silence pydantic serializer warnings on message_stop events ([#338](https://github.com/anthropics/anthropic-sdk-python/pull/338))
- **streaming**: emit input_json events for server tool use blocks ([#336](https://github.com/anthropics/anthropic-sdk-python/pull/336))
- **client**: treat empty ANTHROPIC_API_KEY / ANTHROPIC_AUTH_TOKEN as unset ([#341](https://github.com/anthropics/anthropic-sdk-python/pull/341))
- **bedrock**: expose beta.messages.parse, stream and tool_runner ([#366](https://github.com/anthropics/anthropic-sdk-python/pull/366))
- **vertex**: expose beta.messages.parse and tool_runner ([#367](https://github.com/anthropics/anthropic-sdk-python/pull/367))
- **client**: add models ([`fcb54cf1`](https://github.com/anthropics/anthropic-sdk-python/commit/fcb54cf1))
- **tools**: reject symlink loops in tool paths and skip special skill-archive members ([#322](https://github.com/anthropics/anthropic-sdk-python/pull/322))

## [v0.121.0] - 2026-08-07

> 7 commits since `v0.120.2` · [full diff](https://github.com/anthropics/anthropic-sdk-python/compare/v0.120.2...v0.121.0)

### Added

- **api**: add support for session budgets, advisor tool, pinned inference location and skills auto-loading from GitHub ([`284a5370`](https://github.com/anthropics/anthropic-sdk-python/commit/284a5370))
- **api**: add `mid-conversation-tool-changes-2026-07-01` beta ([`b4cfb5e1`](https://github.com/anthropics/anthropic-sdk-python/commit/b4cfb5e1))
