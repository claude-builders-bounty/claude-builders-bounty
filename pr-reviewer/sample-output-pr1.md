# PR Review: encode/httpx#3698 - support chunked upload in async file-like interfaces

https://github.com/encode/httpx/pull/3698

### Diff overview (computed by `claude-review`, not by the model)

- Files changed: **8** (**+284** / **-6**)
- Changed lines by extension: `.py` 286 lines, `.toml` 2 lines, `.txt` 2 lines
- Test files touched: `tests/test_multipart.py`, `tests/test_content.py`

| File | + | - |
|---|---:|---:|
| `tests/test_multipart.py` | 97 | 0 |
| `tests/test_content.py` | 73 | 0 |
| `httpx/_multipart.py` | 40 | 2 |
| `httpx/_types.py` | 30 | 1 |
| `httpx/_compat.py` | 28 | 0 |
| `httpx/_content.py` | 13 | 2 |
| `pyproject.toml` | 1 | 1 |
| `requirements.txt` | 2 | 0 |

## Summary

The PR adds support for async file-like objects (anyio, trio, aiofiles) as request content and multipart file uploads: a new `AsyncReadableFile` protocol plus the `is_async_readable_file` runtime guard in `httpx/_types.py`, async read loops in `httpx/_content.py` and `httpx/_multipart.py`, a `TypeError` for async files in the sync multipart path, and a version-compat shim in the new `httpx/_compat.py`. When the file's length can be peeked it now sends `Content-Length` instead of chunked transfer encoding, and parametrized tests cover text/binary × PUT/POST content upload and multipart upload against all three libraries.

## Identified risks

- Inconsistent starting-position semantics between the two upload paths. In `httpx/_multipart.py`, `FileField.arender_data` unconditionally does `await self.file.seek(0)` before reading, while the `content=` path (`AsyncIteratorByteStream.__aiter__` in `httpx/_content.py`) streams from the file's current position and `encode_content` declares a `Content-Length` peeked from that same position. The same half-consumed file object therefore uploads its remainder via `content=` but its full contents via `files=`, and if anything reads or seeks the file between request construction (when the header is computed) and streaming, the declared `Content-Length` will not match the bytes sent.
- Length-peeking relies on a sync helper against an async object. `encode_content` in `httpx/_content.py` calls the pre-existing sync `peek_filelike_length` from `httpx/_utils.py` on the async file, but the `AsyncReadableFile` protocol in `httpx/_types.py` only guarantees async `read`/`seek`, a sync `fileno`, and `__aiter__` — it does not guarantee whatever position access the sync helper needs. The new tests assert `fileno_called == 1` and a correct header for the three named libraries, so the happy path works there, but a user object that satisfies `is_async_readable_file` without matching the helper's expectations will misbehave or silently degrade to chunked.
- No rewind for retried requests in the `content=` path. Nothing in `httpx/_content.py` seeks back before streaming, so if httpx needs to send the body again (redirect or auth retry), the file is already at EOF while the headers still carry the original `Content-Length` — the multipart path avoids this via its `seek(0)`, the plain-content path does not.
- Empty files fall back to chunked encoding. `if is_async_readable_file(content) and (content_length_or_none := peek_filelike_length(content)):` in `httpx/_content.py` treats a peeked length of 0 as falsy, so a 0-byte file is sent with `Transfer-Encoding: chunked` instead of `Content-Length: 0`, unlike an equivalent sync file.

## Improvement suggestions

- Decide on one position contract and state it in the `AsyncReadableFile` docs: either always upload from the current position (and drop the `seek(0)` in `httpx/_multipart.py` `arender_data`) or always from offset 0 (and seek in the `content=` path too); add a test that uploads a file whose position is not at 0.
- Give the zero-length case its own branch in `encode_content` (`httpx/_content.py`): check `is not None` instead of truthiness so empty files get `Content-Length: 0`.
- Add a test in `tests/test_content.py` where the same async file object is used for a second request, to pin down the consumed-stream behavior explicitly rather than leaving it accidental.
- Reconsider excluding all of `httpx/_compat.py` from coverage in `pyproject.toml`: the pre-3.10 `aclosing` backport is production code on the older interpreters httpx still supports, and the omit means a regression in it is invisible to CI.
- Document the new accepted type for users (the PR description leaves the docs item unchecked): `FileContent` gaining `AsyncReadableFile` in `httpx/_types.py` and the sync-client `TypeError` in `httpx/_multipart.py` are user-visible behavior worth a docs/changelog note.

## Confidence: Medium

The diff is focused and its happy paths are tested against three real async file libraries, but the position/Content-Length semantics and the protocol-versus-helper contract above cannot be settled from the diff alone and need an explicit decision from the author.
