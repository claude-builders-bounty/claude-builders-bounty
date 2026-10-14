# Review context for encode/httpx#3698

- PR: https://github.com/encode/httpx/pull/3698
- Title: support chunked upload in async file-like interfaces
- Author: tsimoshka
- State: closed
- Base: master <- Head: chunked-async-file-upload

PR description:

# Summary

This PR resolves #1620 and implements chunked upload for `anyio.open_file`, `trio.open_file` and `aiofiles.open_file` when used as `content=` parameter for `post` and `put` request. And implements support for multipart file upload for the same libraries. Most of the code for multipart file upload copied from my old stale PR https://github.com/encode/httpx/pull/3339.

changes:
- `_compat.py` file added to define `TypeIs` and `aclosing` for the range of supported python versions
- `_types.AsyncReadableFile` protocol was added along with `is_async_readable_file` type predicate function to detect and perform type narrowing for trio/asyncio/aiofiles async files
- `_types.FileContent` was extended to include the. `_types.AsyncReadableFile` protocol
- `_content.AsyncIteratorByteStream` updated to use `async read` methods for async files instead of looping over lines
- `_content.encode_content` updated to attach content length header for `_types.AsyncReadableFile` type
- `_multipart.FileField` updated to include async versions of `render` and `render_data`
- `_multipart.MultipartStream` updated with async version of `iter_data` and `__aiter__` method updated to use it
- `test_chunked_async_file_multipart` and `test_chunked_async_file_content` tests are added to test the new functionality
- `aiofiles` and `types-aiofiles` added in requirements to test aiofiles (can be removed with test if aiofiles support is not desirable)

# Checklist

- [x] I understand that this PR may be closed in case there was no previous discussion. (This doesn't apply to typos!)
- [x] I've added a test for each change that was introduced, and I tried as much as possible to make a single atomic change.
- [ ] I've updated the documentation accordingly. (can update if PR is ok otherwise)


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

## Unified diff

```diff
diff --git a/httpx/_compat.py b/httpx/_compat.py
new file mode 100644
index 0000000000..6f8b4c30ef
--- /dev/null
+++ b/httpx/_compat.py
@@ -0,0 +1,28 @@
+import sys
+
+if sys.version_info >= (3, 10):
+    from contextlib import aclosing
+else:
+    from contextlib import asynccontextmanager
+    from typing import Any, AsyncIterator, Awaitable, Protocol, TypeVar
+
+    class _SupportsAclose(Protocol):
+        def aclose(self) -> Awaitable[object]: ...
+
+    _SupportsAcloseT = TypeVar("_SupportsAcloseT", bound=_SupportsAclose)
+
+    @asynccontextmanager
+    async def aclosing(thing: _SupportsAcloseT) -> AsyncIterator[Any]:
+        try:
+            yield thing
+        finally:
+            await thing.aclose()
+
+
+if sys.version_info >= (3, 13):
+    from typing import TypeIs
+else:
+    from typing_extensions import TypeIs
+
+
+__all__ = ["aclosing", "TypeIs"]
diff --git a/httpx/_content.py b/httpx/_content.py
index 6f479a0885..8f88bf63b8 100644
--- a/httpx/_content.py
+++ b/httpx/_content.py
@@ -22,8 +22,9 @@
     RequestFiles,
     ResponseContent,
     SyncByteStream,
+    is_async_readable_file,
 )
-from ._utils import peek_filelike_length, primitive_value_to_str
+from ._utils import peek_filelike_length, primitive_value_to_str, to_bytes
 
 __all__ = ["ByteStream"]
 
@@ -83,6 +84,11 @@ async def __aiter__(self) -> AsyncIterator[bytes]:
             while chunk:
                 yield chunk
                 chunk = await self._stream.aread(self.CHUNK_SIZE)
+        elif is_async_readable_file(self._stream):
+            chunk = await self._stream.read(self.CHUNK_SIZE)
+            while chunk:
+                yield to_bytes(chunk)
+                chunk = await self._stream.read(self.CHUNK_SIZE)
         else:
             # Otherwise iterate.
             async for part in self._stream:
@@ -127,7 +133,12 @@ def encode_content(
         return headers, IteratorByteStream(content)  # type: ignore
 
     elif isinstance(content, AsyncIterable):
-        headers = {"Transfer-Encoding": "chunked"}
+        if is_async_readable_file(content) and (
+            content_length_or_none := peek_filelike_length(content)
+        ):
+            headers = {"Content-Length": str(content_length_or_none)}
+        else:
+            headers = {"Transfer-Encoding": "chunked"}
         return headers, AsyncIteratorByteStream(content)
 
     raise TypeError(f"Unexpected type for 'content', {type(content)!r}")
diff --git a/httpx/_multipart.py b/httpx/_multipart.py
index b4761af9b2..298a1ab347 100644
--- a/httpx/_multipart.py
+++ b/httpx/_multipart.py
@@ -7,6 +7,7 @@
 import typing
 from pathlib import Path
 
+from ._compat import aclosing
 from ._types import (
     AsyncByteStream,
     FileContent,
@@ -14,6 +15,7 @@
     RequestData,
     RequestFiles,
     SyncByteStream,
+    is_async_readable_file,
 )
 from ._utils import (
     peek_filelike_length,
@@ -201,6 +203,11 @@ def render_headers(self) -> bytes:
         return self._headers
 
     def render_data(self) -> typing.Iterator[bytes]:
+        if is_async_readable_file(self.file):
+            raise TypeError(
+                "Invalid type for file. AsyncReadableFile is not supported."
+            )
+
         if isinstance(self.file, (str, bytes)):
             yield to_bytes(self.file)
             return
@@ -216,10 +223,27 @@ def render_data(self) -> typing.Iterator[bytes]:
             yield to_bytes(chunk)
             chunk = self.file.read(self.CHUNK_SIZE)
 
+    async def arender_data(self) -> typing.AsyncGenerator[bytes]:
+        if not is_async_readable_file(self.file):
+            for chunk in self.render_data():
+                yield chunk
+            return
+        await self.file.seek(0)
+        chunk = await self.file.read(self.CHUNK_SIZE)
+        while chunk:
+            yield to_bytes(chunk)
+            chunk = await self.file.read(self.CHUNK_SIZE)
+
     def render(self) -> typing.Iterator[bytes]:
         yield self.render_headers()
         yield from self.render_data()
 
+    async def arender(self) -> typing.AsyncGenerator[bytes]:
+        yield self.render_headers()
+        async with aclosing(self.arender_data()) as data:
+            async for chunk in data:
+                yield chunk
+
 
 class MultipartStream(SyncByteStream, AsyncByteStream):
     """
@@ -262,6 +286,19 @@ def iter_chunks(self) -> typing.Iterator[bytes]:
             yield b"\r\n"
         yield b"--%s--\r\n" % self.boundary
 
+    async def aiter_chunks(self) -> typing.AsyncGenerator[bytes]:
+        for field in self.fields:
+            yield b"--%s\r\n" % self.boundary
+            if isinstance(field, FileField):
+                async with aclosing(field.arender()) as data:
+                    async for chunk in data:
+                        yield chunk
+            else:
+                for chunk in field.render():
+                    yield chunk
+            yield b"\r\n"
+        yield b"--%s--\r\n" % self.boundary
+
     def get_content_length(self) -> int | None:
         """
         Return the length of the multipart encoded content, or `None` if
@@ -296,5 +333,6 @@ def __iter__(self) -> typing.Iterator[bytes]:
             yield chunk
 
     async def __aiter__(self) -> typing.AsyncIterator[bytes]:
-        for chunk in self.iter_chunks():
-            yield chunk
+        async with aclosing(self.aiter_chunks()) as data:
+            async for chunk in data:
+                yield chunk
diff --git a/httpx/_types.py b/httpx/_types.py
index 704dfdffc8..897b87f006 100644
--- a/httpx/_types.py
+++ b/httpx/_types.py
@@ -2,11 +2,13 @@
 Type definitions for type checking purposes.
 """
 
+import inspect
 from http.cookiejar import CookieJar
 from typing import (
     IO,
     TYPE_CHECKING,
     Any,
+    AnyStr,
     AsyncIterable,
     AsyncIterator,
     Callable,
@@ -16,11 +18,14 @@
     List,
     Mapping,
     Optional,
+    Protocol,
     Sequence,
     Tuple,
     Union,
 )
 
+from ._compat import TypeIs
+
 if TYPE_CHECKING:  # pragma: no cover
     from ._auth import Auth  # noqa: F401
     from ._config import Proxy, Timeout  # noqa: F401
@@ -71,7 +76,18 @@
 
 RequestData = Mapping[str, Any]
 
-FileContent = Union[IO[bytes], bytes, str]
+
+class AsyncReadableFile(Protocol):
+    async def __aiter__(self) -> AsyncIterator[AnyStr]: ...
+
+    async def read(self, size: int = -1) -> AnyStr: ...
+
+    def fileno(self) -> int: ...
+
+    async def seek(self, offset: int, whence: Optional[int] = ...) -> int: ...
+
+
+FileContent = Union[IO[bytes], bytes, str, AsyncReadableFile]
 FileTypes = Union[
     # file (or bytes)
     FileContent,
@@ -112,3 +128,16 @@ async def __aiter__(self) -> AsyncIterator[bytes]:
 
     async def aclose(self) -> None:
         pass
+
+
+def is_async_readable_file(fp: Any) -> TypeIs[AsyncReadableFile]:
+    return (
+        isinstance(fp, AsyncIterable)
+        and hasattr(fp, "read")
+        and inspect.iscoroutinefunction(fp.read)
+        and hasattr(fp, "fileno")
+        and callable(fp.fileno)
+        and not inspect.iscoroutinefunction(fp.fileno)
+        and hasattr(fp, "seek")
+        and inspect.iscoroutinefunction(fp.seek)
+    )
diff --git a/pyproject.toml b/pyproject.toml
index fc3e95ea74..6f2f6f575c 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -128,5 +128,5 @@ markers = [
 ]
 
 [tool.coverage.run]
-omit = ["venv/*"]
+omit = ["venv/*", "httpx/_compat.py"]
 include = ["httpx/*", "tests/*"]
diff --git a/requirements.txt b/requirements.txt
index ebc6ea7fc5..0f6683aff7 100644
--- a/requirements.txt
+++ b/requirements.txt
@@ -27,3 +27,5 @@ trio==0.31.0
 trio-typing==0.10.0
 trustme==1.2.1
 uvicorn==0.35.0
+aiofiles==25.1.0
+types-aiofiles==25.1.0.20251011
diff --git a/tests/test_content.py b/tests/test_content.py
index 9bfe983722..135197a3a5 100644
--- a/tests/test_content.py
+++ b/tests/test_content.py
@@ -1,9 +1,14 @@
 import io
 import typing
 
+import aiofiles
+import anyio
 import pytest
+import trio
 
 import httpx
+from httpx._content import AsyncIteratorByteStream
+from httpx._types import AsyncReadableFile, is_async_readable_file
 
 method = "POST"
 url = "https://www.example.com"
@@ -516,3 +521,71 @@ def test_allow_nan_false():
         ValueError, match="Out of range float values are not JSON compliant"
     ):
         httpx.Response(200, json=data_with_inf)
+
+
+@pytest.mark.parametrize(
+    "client_method,content_seed,mode",
+    [
+        ("put", "a🥳", "rt"),
+        ("post", "a🥳", "rt"),
+        ("put", "a🥳", "rb"),
+        ("post", "a🥳", "rb"),
+    ],
+    ids=["put_text", "post_text", "put_binary", "post_binary"],
+)
+@pytest.mark.anyio
+async def test_chunked_async_file_content(
+    tmp_path, anyio_backend, monkeypatch, client_method, server, content_seed, mode
+):
+    total_chunks = 3
+    seed_size = len(content_seed.encode()) if "b" in mode else len(content_seed)
+    read_calls_expected = total_chunks * seed_size + 1
+    content = "".join(
+        [content_seed * AsyncIteratorByteStream.CHUNK_SIZE] * total_chunks
+    )
+    content_bytes = content.encode()
+    to_upload = tmp_path / "upload.txt"
+    to_upload.write_bytes(content_bytes)
+    url = server.url.copy_with(path="/echo_body")
+
+    async def checks(client: httpx.AsyncClient, async_file: AsyncReadableFile) -> None:
+        read_called = 0
+        fileno_called = 0
+        original_read = async_file.read
+        original_fileno = async_file.fileno
+
+        async def mock_read(*args, **kwargs):
+            nonlocal read_called
+            read_called += 1
+            return await original_read(*args, **kwargs)
+
+        def mock_fileno(*args):
+            nonlocal fileno_called
+            fileno_called += 1
+            return original_fileno(*args)
+
+        monkeypatch.setattr(async_file, "read", mock_read)
+        monkeypatch.setattr(async_file, "fileno", mock_fileno)
+        response = await getattr(client, client_method)(url=url, content=async_file)
+        assert response.status_code == 200
+        assert response.content == content_bytes
+        assert response.request.headers["Content-Length"] == str(len(content_bytes))
+        assert read_called == read_calls_expected
+        assert fileno_called == 1
+
+    async with (
+        await anyio.open_file(to_upload, mode=mode)
+        if anyio_backend != "trio"
+        else await trio.open_file(to_upload, mode=mode) as async_file,
+        httpx.AsyncClient() as client,
+    ):
+        assert is_async_readable_file(async_file)
+        await checks(client, async_file)
+
+    if anyio_backend != "trio":  # aiofiles doesn't work with trio
+        async with (
+            aiofiles.open(to_upload, mode=mode) as aio_file,
+            httpx.AsyncClient() as client,
+        ):
+            assert is_async_readable_file(aio_file)
+            await checks(client, aio_file)
diff --git a/tests/test_multipart.py b/tests/test_multipart.py
index 764f85a253..64bc63bd04 100644
--- a/tests/test_multipart.py
+++ b/tests/test_multipart.py
@@ -4,9 +4,13 @@
 import tempfile
 import typing
 
+import anyio
 import pytest
+import trio
 
 import httpx
+from httpx._multipart import FileField
+from httpx._types import AsyncReadableFile, is_async_readable_file
 
 
 def echo_request_content(request: httpx.Request) -> httpx.Response:
@@ -467,3 +471,96 @@ def test_unicode_with_control_character(self):
         files = {"upload": (filename, b"<file content>")}
         request = httpx.Request("GET", "https://www.example.com", files=files)
         assert expected in request.read()
+
+
+@pytest.mark.parametrize(
+    "content_seed,mode",
+    [
+        ("a🥳", "rt"),
+        ("a🥳", "rb"),
+    ],
+    ids=["text_mode", "binary_mode"],
+)
+@pytest.mark.anyio
+async def test_chunked_async_file_multipart(
+    tmp_path, anyio_backend, monkeypatch, server, content_seed, mode
+):
+    total_chunks = 3
+    seed_size = len(content_seed.encode()) if "b" in mode else len(content_seed)
+    read_calls_expected = total_chunks * seed_size + 1
+    content = "".join([content_seed * FileField.CHUNK_SIZE] * total_chunks)
+    content_bytes = content.encode()
+    to_upload = tmp_path / "upload.txt"
+    to_upload.write_bytes(content_bytes)
+    url = server.url.copy_with(path="/echo_body")
+
+    async def checks(client: httpx.AsyncClient, async_file: AsyncReadableFile) -> None:
+        read_called = 0
+        fileno_called = False
+        original_read = async_file.read
+        original_fileno = async_file.fileno
+
+        async def mock_read(*args, **kwargs):
+            nonlocal read_called
+            read_called += 1
+            return await original_read(*args, **kwargs)
+
+        def mock_fileno(*args):
+            nonlocal fileno_called
+            fileno_called = True
+            return original_fileno(*args)
+
+        monkeypatch.setattr(async_file, "read", mock_read)
+        monkeypatch.setattr(async_file, "fileno", mock_fileno)
+        response = await client.post(url=url, files={"file": async_file})
+        assert response.status_code == 200
+        boundary = response.request.headers["Content-Type"].split("boundary=")[-1]
+        boundary_bytes = boundary.encode("ascii")
+        pre_content = b"".join(
+            [
+                b"--" + boundary_bytes + b"\r\n",
+                b'Content-Disposition: form-data; name="file"; '
+                b'filename="upload.txt"\r\n',
+                b"Content-Type: text/plain\r\n",
+                b"\r\n",
+            ]
+        )
+        post_content = b"".join(
+            [
+                b"\r\n",
+                b"--" + boundary_bytes + b"--\r\n",
+            ]
+        )
+        assert response.content == b"".join(
+            [
+                pre_content,
+                content_bytes,
+                post_content,
+            ]
+        )
+        assert response.request.headers["Content-Length"] == str(
+            len(pre_content) + len(post_content) + len(content_bytes)
+        )
+        assert read_called == read_calls_expected
+        assert fileno_called
+
+    async with (
+        await anyio.open_file(to_upload, mode=mode)
+        if anyio_backend != "trio"
+        else await trio.open_file(to_upload, mode=mode) as async_file,
+        httpx.AsyncClient() as client,
+    ):
+        assert is_async_readable_file(async_file)
+
+        await checks(client, async_file)
+
+    async with (
+        await anyio.open_file(to_upload, mode=mode)
+        if anyio_backend != "trio"
+        else await trio.open_file(to_upload, mode=mode) as async_file,
+    ):
+        with (
+            httpx.Client() as sync_client,
+            pytest.raises(TypeError, match="AsyncReadableFile is not supported"),
+        ):
+            sync_client.post(url, files={"file": async_file})

```
