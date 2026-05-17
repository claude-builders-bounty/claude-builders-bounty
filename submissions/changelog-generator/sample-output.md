# Changelog

> psf/requests

## [v2.34.2] — 2026-05-17

### ✨ Added

- 3.14t support to CI (#7419) ([`eb173bc`](https://github.com/psf/requests/commit/eb173bc))
- inline types to Requests (#7272) ([`561e4b6`](https://github.com/psf/requests/commit/561e4b6))
- tests for hasattr/getattr usage on LookupDict (#7401) ([`8f6cda9`](https://github.com/psf/requests/commit/8f6cda9))
- groups for GHA and pre-commit dependabot PRs (#7387) ([`9450dd5`](https://github.com/psf/requests/commit/9450dd5))
- Zizmor workflow and make initial updates ([`cbce031`](https://github.com/psf/requests/commit/cbce031))

### 🔄 Changed

- v2.34.2 ([`6e83187`](https://github.com/psf/requests/commit/6e83187))
- Move Request.headers back to Mapping (#7441) ([`84d10f0`](https://github.com/psf/requests/commit/84d10f0))
- v2.34.1 ([`b7b549b`](https://github.com/psf/requests/commit/b7b549b))
- JsonType containers to read-based collections (#7436) ([`5691f59`](https://github.com/psf/requests/commit/5691f59))
- Constrain Response.reason to str (#7437) ([`2144213`](https://github.com/psf/requests/commit/2144213))
- v2.34.0 ([`0b401c7`](https://github.com/psf/requests/commit/0b401c7))
- Align Session.get parameters with requests.get (#7429) ([`86b378d`](https://github.com/psf/requests/commit/86b378d))
- Port bpo-39057 to Requests (#7427) ([`a4f9a59`](https://github.com/psf/requests/commit/a4f9a59))
- Parameterize SupportsItems to handle Mapping key invariance (#7426) ([`3816cfa`](https://github.com/psf/requests/commit/3816cfa))
- fix hooks type (#7425) ([`b684dcb`](https://github.com/psf/requests/commit/b684dcb))
- Formalize 3.15 support (#7422) ([`dc9dbdf`](https://github.com/psf/requests/commit/dc9dbdf))
- Clear proxy env vars before every test run (#7423) ([`25340eb`](https://github.com/psf/requests/commit/25340eb))
- Preserve leading slashes in request path_url (#7315) ([`fd62809`](https://github.com/psf/requests/commit/fd62809))
- docs: Fix missing hook output in docs example (#7421) ([`e8d2c01`](https://github.com/psf/requests/commit/e8d2c01))
- docs: update stale Sphinx link in contributing guide ([`f64a0d7`](https://github.com/psf/requests/commit/f64a0d7))
- https://github.com/astral-sh/ruff-pre-commit (#7411) ([`04d7505`](https://github.com/psf/requests/commit/04d7505))
- v2.34.0.dev1 ([`f7822f7`](https://github.com/psf/requests/commit/f7822f7))
- Ruff rule UP038 has been removed (#7393) ([`6ec76b4`](https://github.com/psf/requests/commit/6ec76b4))
- https://github.com/astral-sh/ruff-pre-commit (#7390) ([`f43f750`](https://github.com/psf/requests/commit/f43f750))
- index.rst to match README info (#7386) ([`93bf533`](https://github.com/psf/requests/commit/93bf533))
- pypa/gh-action-pypi-publish from 1.13.0 to 1.14.0 (#7378) ([`79f4df8`](https://github.com/psf/requests/commit/79f4df8))
- Consider urllib3 version has 3 numbers at most (#7375) (#7376) ([`b294b08`](https://github.com/psf/requests/commit/b294b08))
- README and remove extraneous images (#7366) ([`514c162`](https://github.com/psf/requests/commit/514c162))
- Clarify decode_unicode behaviour in iter_{content,lines} docstrings (#7365) ([`d2f6bde`](https://github.com/psf/requests/commit/d2f6bde))
- Move DigestAuth hash algorithms to use usedforsecurity=False (#7310) ([`a044b02`](https://github.com/psf/requests/commit/a044b02))
- Move pytest pin to support 9.x series (#7364) ([`16df2a0`](https://github.com/psf/requests/commit/16df2a0))
- Don't hide navigation on mobile webpage (#7360) ([`fe2063b`](https://github.com/psf/requests/commit/fe2063b))
- pre-commit versions (#7348) ([`4b0b1a3`](https://github.com/psf/requests/commit/4b0b1a3))
- Prevent Response self-reference in redirect history (#7328) ([`ef439eb`](https://github.com/psf/requests/commit/ef439eb))
- github/codeql-action from 4.34.1 to 4.35.1 ([`6360477`](https://github.com/psf/requests/commit/6360477))
- v2.33.1 ([`111d2b7`](https://github.com/psf/requests/commit/111d2b7))
- DRY out extras definition (#7277) ([`7407309`](https://github.com/psf/requests/commit/7407309))
- v2.33.0 ([`bc04dfd`](https://github.com/psf/requests/commit/bc04dfd))
- Merge commit from fork ([`66d21cb`](https://github.com/psf/requests/commit/66d21cb))
- Move badges to top of README (#7293) ([`8b9bc8f`](https://github.com/psf/requests/commit/8b9bc8f))

### 🐛 Fixed

- mutability issues with headers input types (#7431) ([`e511bc7`](https://github.com/psf/requests/commit/e511bc7))
- `prepare_body` stream detection for `__getattr__`-based file wrappers (#7433) ([`6404f34`](https://github.com/psf/requests/commit/6404f34))
- remaining typos (#7395) ([`27e0981`](https://github.com/psf/requests/commit/27e0981))
- typos discovered by codespell (#7371) ([`5f3ff9b`](https://github.com/psf/requests/commit/5f3ff9b))
- malformed value parsing for Content-Type (#7309) ([`f0198e6`](https://github.com/psf/requests/commit/f0198e6))
- cosmetic header validity parsing regex (#7308) ([`bc7dd0f`](https://github.com/psf/requests/commit/bc7dd0f))
- unintended test extra (#7306) ([`4443b1a`](https://github.com/psf/requests/commit/4443b1a))

### 🗑️ Removed

- remaining http:// reference URIs ([`d60f477`](https://github.com/psf/requests/commit/d60f477))
- docs and add i18n wrappers (#7354) ([`185f587`](https://github.com/psf/requests/commit/185f587))
- extracted file after extract_zipped_path test (#7305) ([`389eea5`](https://github.com/psf/requests/commit/389eea5))

---
*Auto-generated by changelog.py on 2026-05-17 17:44:18*
