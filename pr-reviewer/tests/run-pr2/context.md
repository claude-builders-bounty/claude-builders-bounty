# Review context for pallets/flask#6168

- PR: https://github.com/pallets/flask/pull/6168
- Title: drop support for Python 3.10
- Author: davidism
- State: closed (merged)
- Base: main <- Head: drop-eol-python

PR description:

3.10 is EOL within six months of feature release. https://devguide.python.org/versions/
https://palletsprojects.com/versions

### Diff overview (computed by `claude-review`, not by the model)

- Files changed: **12** (**+67** / **-433**)
- Changed lines by extension: `.lock` 429 lines, `.py` 50 lines, `.toml` 14 lines, `.rst` 4 lines, `.yaml` 3 lines
- Test files touched: `tests/test_appctx.py`, `tests/test_basic.py`, `tests/test_json_tag.py`, `.github/workflows/tests.yaml`, `tests/test_config.py`

| File | + | - |
|---|---:|---:|
| `uv.lock` | 40 | 389 |
| `tests/test_appctx.py` | 11 | 17 |
| `pyproject.toml` | 4 | 10 |
| `tests/test_basic.py` | 3 | 3 |
| `src/flask/helpers.py` | 1 | 4 |
| `src/flask/sessions.py` | 2 | 2 |
| `tests/test_json_tag.py` | 2 | 2 |
| `.github/workflows/tests.yaml` | 1 | 2 |
| `CHANGES.rst` | 1 | 1 |
| `docs/installation.rst` | 1 | 1 |
| `tests/test_config.py` | 1 | 1 |
| `src/flask/cli.py` | 0 | 1 |

## Unified diff

```diff
diff --git a/.github/workflows/tests.yaml b/.github/workflows/tests.yaml
index f67b1e398c..a8991315db 100644
--- a/.github/workflows/tests.yaml
+++ b/.github/workflows/tests.yaml
@@ -25,10 +25,9 @@ jobs:
           - {python: '3.13'}
           - {python: '3.12'}
           - {python: '3.11'}
-          - {python: '3.10'}
           - {name: PyPy, python: 'pypy-3.11', tox: pypy3.11}
           - {name: Minimum Versions, python: '3.14', tox: tests-min}
-          - {name: Development Versions, python: '3.10', tox: tests-dev}
+          - {name: Development Versions, python: '3.11', tox: tests-dev}
     steps:
       - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1 # v7.0.1
         with:
diff --git a/CHANGES.rst b/CHANGES.rst
index 129b58e7b5..21c0c5abeb 100644
--- a/CHANGES.rst
+++ b/CHANGES.rst
@@ -3,7 +3,7 @@ Version 3.2.0
 
 Unreleased
 
--   Drop support for Python 3.9. :pr:`5730`
+-   Drop support for Python 3.9 and 3.10. :pr:`5730` :pr:`6166`
 -   Remove previously deprecated code: ``__version__``. :pr:`5648`
 -   ``RequestContext`` has merged with ``AppContext``. ``RequestContext`` is now
     a deprecated alias. If an app context is already pushed, it is not reused
diff --git a/docs/installation.rst b/docs/installation.rst
index f3a8ab24a0..453aa73e61 100644
--- a/docs/installation.rst
+++ b/docs/installation.rst
@@ -5,7 +5,7 @@ Installation
 Python Version
 --------------
 
-We recommend using the latest version of Python. Flask supports Python 3.10 and newer.
+We recommend using the latest version of Python. Flask supports Python 3.11 and newer.
 
 
 Dependencies
diff --git a/pyproject.toml b/pyproject.toml
index ef28fccb8c..05a59c4739 100644
--- a/pyproject.toml
+++ b/pyproject.toml
@@ -19,7 +19,7 @@ classifiers = [
     "Topic :: Software Development :: Libraries :: Application Frameworks",
     "Typing :: Typed",
 ]
-requires-python = ">=3.10"
+requires-python = ">=3.11"
 dependencies = [
     "blinker>=1.9.0",
     "click>=8.1.3",
@@ -124,7 +124,7 @@ exclude_also = [
 ]
 
 [tool.mypy]
-python_version = "3.10"
+python_version = "3.11"
 files = ["src", "tests/type_check"]
 show_error_codes = true
 pretty = true
@@ -139,11 +139,6 @@ module = [
 ]
 ignore_missing_imports = true
 
-[tool.pyright]
-pythonVersion = "3.10"
-include = ["src", "tests/type_check"]
-typeCheckingMode = "basic"
-
 [tool.ruff]
 src = ["src"]
 fix = true
@@ -171,7 +166,7 @@ ignore-words-list = "te"
 env_list = [
     "py3.15",
     "py3.14", "py3.14t",
-    "py3.13", "py3.12", "py3.11", "py3.10",
+    "py3.13", "py3.12", "py3.11",
     "pypy3.11",
     "tests-min", "tests-dev",
     "style",
@@ -214,7 +209,7 @@ commands = [
 
 [tool.tox.env.tests-dev]
 description = "pytest on development dependency versions (git main branch)"
-base_python = ["3.10"]
+base_python = ["3.11"]
 commands = [
     [
         "uv", "pip", "install",
@@ -242,7 +237,6 @@ description = "run static type checkers"
 dependency_groups = ["typing"]
 commands = [
     ["mypy"],
-    ["pyright"],
 ]
 
 [tool.tox.env.docs]
diff --git a/src/flask/cli.py b/src/flask/cli.py
index 53b4e6752d..c4ce9ba6f1 100644
--- a/src/flask/cli.py
+++ b/src/flask/cli.py
@@ -874,7 +874,6 @@ def convert(
         self, value: t.Any, param: click.Parameter | None, ctx: click.Context | None
     ) -> t.Any:
         items = self.split_envvar_value(value)
-        # can't call no-arg super() inside list comprehension until Python 3.12
         super_convert = super().convert
         return [super_convert(item, param, ctx) for item in items]
 
diff --git a/src/flask/helpers.py b/src/flask/helpers.py
index e479f1814a..5073bea8f8 100644
--- a/src/flask/helpers.py
+++ b/src/flask/helpers.py
@@ -676,7 +676,4 @@ def __exit__(
     def raise_any(self, message: str) -> None:
         """Raise if any errors were collected."""
         if self.errors:
-            if sys.version_info >= (3, 11):
-                raise BaseExceptionGroup(message, self.errors)  # noqa: F821
-            else:
-                raise self.errors[0]
+            raise BaseExceptionGroup(message, self.errors)
diff --git a/src/flask/sessions.py b/src/flask/sessions.py
index ad357706ff..1e76b743ef 100644
--- a/src/flask/sessions.py
+++ b/src/flask/sessions.py
@@ -5,7 +5,7 @@
 import typing as t
 from collections.abc import MutableMapping
 from datetime import datetime
-from datetime import timezone
+from datetime import UTC
 
 from itsdangerous import BadSignature
 from itsdangerous import URLSafeTimedSerializer
@@ -227,7 +227,7 @@ def get_expiration_time(self, app: Flask, session: SessionMixin) -> datetime | N
         lifetime configured on the application.
         """
         if session.permanent:
-            return datetime.now(timezone.utc) + app.permanent_session_lifetime
+            return datetime.now(UTC) + app.permanent_session_lifetime
         return None
 
     def should_set_cookie(self, app: Flask, session: SessionMixin) -> bool:
diff --git a/tests/test_appctx.py b/tests/test_appctx.py
index 2d4eecc520..34929569ce 100644
--- a/tests/test_appctx.py
+++ b/tests/test_appctx.py
@@ -1,5 +1,3 @@
-import sys
-
 import pytest
 
 import flask
@@ -246,20 +244,16 @@ def app_signal(sender: flask.Flask, exc: Exception | None) -> None:
         flask.request_tearing_down.connected_to(request_signal, app),
         flask.appcontext_tearing_down.connected_to(app_signal, app),
     ):
-        if sys.version_info >= (3, 11):
-            with pytest.raises(ExceptionGroup, match="context teardown") as exc_info:  # noqa: F821
-                client.get()
-
-            assert len(exc_info.value.exceptions) == 2
-            eg1, eg2 = exc_info.value.exceptions
-            assert isinstance(eg1, ExceptionGroup)  # noqa: F821
-            assert "request teardown" in eg1.message
-            assert len(eg1.exceptions) == 2
-            assert isinstance(eg2, ExceptionGroup)  # noqa: F821
-            assert "app teardown" in eg2.message
-            assert len(eg2.exceptions) == 2
-        else:
-            with pytest.raises(ValueError, match="request_teardown"):
-                client.get()
+        with pytest.raises(ExceptionGroup, match="context teardown") as exc_info:  # noqa: F821
+            client.get()
+
+        assert len(exc_info.value.exceptions) == 2
+        eg1, eg2 = exc_info.value.exceptions
+        assert isinstance(eg1, ExceptionGroup)  # noqa: F821
+        assert "request teardown" in eg1.message
+        assert len(eg1.exceptions) == 2
+        assert isinstance(eg2, ExceptionGroup)  # noqa: F821
+        assert "app teardown" in eg2.message
+        assert len(eg2.exceptions) == 2
 
     assert count == 4
diff --git a/tests/test_basic.py b/tests/test_basic.py
index b370f4f7e1..3dc343b9c3 100644
--- a/tests/test_basic.py
+++ b/tests/test_basic.py
@@ -6,7 +6,7 @@
 import weakref
 from contextlib import nullcontext
 from datetime import datetime
-from datetime import timezone
+from datetime import UTC
 from functools import partial
 from platform import python_implementation
 
@@ -438,7 +438,7 @@ def test():
     assert "set-cookie" in rv.headers
     match = re.search(r"(?i)\bexpires=([^;]+)", rv.headers["set-cookie"])
     expires = parse_date(match.group())
-    expected = datetime.now(timezone.utc) + app.permanent_session_lifetime
+    expected = datetime.now(UTC) + app.permanent_session_lifetime
     assert expires.year == expected.year
     assert expires.month == expected.month
     assert expires.day == expected.day
@@ -468,7 +468,7 @@ def dump_session_contents():
 
 
 def test_session_special_types(app, client):
-    now = datetime.now(timezone.utc).replace(microsecond=0)
+    now = datetime.now(UTC).replace(microsecond=0)
     the_uuid = uuid.uuid4()
 
     @app.route("/")
diff --git a/tests/test_config.py b/tests/test_config.py
index e5b1906e7c..6c80bfa1b1 100644
--- a/tests/test_config.py
+++ b/tests/test_config.py
@@ -1,5 +1,6 @@
 import json
 import os
+import tomllib
 
 import pytest
 
@@ -36,7 +37,6 @@ def test_config_from_file_json():
 
 
 def test_config_from_file_toml():
-    tomllib = pytest.importorskip("tomllib", reason="tomllib added in 3.11")
     app = flask.Flask(__name__)
     current_dir = os.path.dirname(os.path.abspath(__file__))
     app.config.from_file(
diff --git a/tests/test_json_tag.py b/tests/test_json_tag.py
index 677160a636..57d2045939 100644
--- a/tests/test_json_tag.py
+++ b/tests/test_json_tag.py
@@ -1,5 +1,5 @@
 from datetime import datetime
-from datetime import timezone
+from datetime import UTC
 from uuid import uuid4
 
 import pytest
@@ -21,7 +21,7 @@
         b"\xff",
         Markup("<html>"),
         uuid4(),
-        datetime.now(tz=timezone.utc).replace(microsecond=0),
+        datetime.now(tz=UTC).replace(microsecond=0),
     ),
 )
 def test_dump_load_unchanged(data):
diff --git a/uv.lock b/uv.lock
index 6f3aae9764..8ac3a448fd 100644
--- a/uv.lock
+++ b/uv.lock
@@ -1,11 +1,10 @@
 version = 1
 revision = 3
-requires-python = ">=3.10"
+requires-python = ">=3.11"
 resolution-markers = [
     "python_full_version >= '3.15'",
     "python_full_version >= '3.12' and python_full_version < '3.15'",
-    "python_full_version == '3.11.*'",
-    "python_full_version < '3.11'",
+    "python_full_version < '3.12'",
 ]
 
 [[package]]
@@ -22,7 +21,6 @@ name = "anyio"
 version = "4.14.2"
 source = { registry = "https://pypi.org/simple" }
 dependencies = [
-    { name = "exceptiongroup", marker = "python_full_version < '3.11'" },
     { name = "idna" },
     { name = "typing-extensions", marker = "python_full_version < '3.13'" },
 ]
@@ -35,9 +33,6 @@ wheels = [
 name = "asgiref"
 version = "3.12.1"
 source = { registry = "https://pypi.org/simple" }
-dependencies = [
-    { name = "typing-extensions", marker = "python_full_version < '3.11'" },
-]
 sdist = { url = "https://files.pythonhosted.org/packages/e6/26/3b59f2bdae5f640389becb1f673cded775287f5fc4f816309d9ca9a3f93d/asgiref-3.12.1.tar.gz", hash = "sha256:59dcb51c272ad209d59bed5708a64a333083e86017d7fcdd67498eeab7784340", size = 42378, upload-time = "2026-07-14T09:56:18.087Z" }
 wheels = [
     { url = "https://files.pythonhosted.org/packages/c0/1b/54f4ad77cd8a584fa70746c47df988e002cf1ee1eba43364d46f87803647/asgiref-3.12.1-py3-none-any.whl", hash = "sha256:fe386d1c2bff7259ea95929266d12a8cf9a8b5a1c2598402967d8792e7a7c094", size = 25478, upload-time = "2026-07-14T09:56:16.926Z" },
@@ -129,18 +124,6 @@ dependencies = [
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/57/5f/ff100cae70ebe9d8df1c01a00e510e45d9adb5c1fdda84791b199141de97/cffi-2.1.0.tar.gz", hash = "sha256:efc1cdd798b1aaf39b4610bba7aad28c9bea9b910f25c784ccf9ec1fa719d1f9", size = 531036, upload-time = "2026-07-06T21:34:30.382Z" }
 wheels = [
-    { url = "https://files.pythonhosted.org/packages/c0/e9/6d7724983b3d5a0908dbf74f64038ade77c18646ff6636ec7894fd392ce1/cffi-2.1.0-cp310-cp310-macosx_10_15_x86_64.whl", hash = "sha256:b65f590ef2a44640f9a05dbb548a429b4ade77913ce683ac8b1480777658a6c0", size = 183837, upload-time = "2026-07-06T21:32:09.655Z" },
-    { url = "https://files.pythonhosted.org/packages/69/aa/24580a278de21fd7322635556334d9b535f1cbc00b0a3919447cdf464c65/cffi-2.1.0-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:164bff1657b2a74f0b6d54e11c9b375bc97b931f2ca9c43fcf875838da1570dd", size = 184226, upload-time = "2026-07-06T21:32:11.196Z" },
-    { url = "https://files.pythonhosted.org/packages/88/a9/02cae418ec4beb282ace11958d9d4737793439d561fadc7e6d56f2e2b354/cffi-2.1.0-cp310-cp310-manylinux1_i686.manylinux2014_i686.manylinux_2_17_i686.manylinux_2_5_i686.whl", hash = "sha256:c941bb58d5a6e1c3892d86e42927ed6c180302f07e6d395d08c416e594b98b46", size = 211107, upload-time = "2026-07-06T21:32:12.328Z" },
-    { url = "https://files.pythonhosted.org/packages/3b/30/c806937ed5e4c2c7ac30d9d6b76b5dc57ff8b75d83800d9bb11a8253cf2a/cffi-2.1.0-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.whl", hash = "sha256:a016194dbe13d14ee9556e734b772d8d67b947092b268d757fd4290e3ba2dfc2", size = 218733, upload-time = "2026-07-06T21:32:13.67Z" },
-    { url = "https://files.pythonhosted.org/packages/f9/cf/398272b8bbfd58aa314fda5a7f1cdbb26d1d78ae324a11211521315dd1f0/cffi-2.1.0-cp310-cp310-manylinux2014_ppc64le.manylinux_2_17_ppc64le.whl", hash = "sha256:03e9810d18c646077e501f661b682fbf5dee4676048527ca3cffe66faa9960dd", size = 205543, upload-time = "2026-07-06T21:32:15.148Z" },
-    { url = "https://files.pythonhosted.org/packages/45/ca/f91641185cdd90c36d317a9dc7f85e88ef8682d8b300977baff5e23c35d8/cffi-2.1.0-cp310-cp310-manylinux2014_s390x.manylinux_2_17_s390x.whl", hash = "sha256:19c54ac121cad98450b4896fa9a43ee0180d57bc4bc911a33db6cab1efab6cd3", size = 205460, upload-time = "2026-07-06T21:32:16.479Z" },
-    { url = "https://files.pythonhosted.org/packages/38/66/04781a77b411f0bb5b234d62c1814754ab75ebe455ccff1b08e8d7aae98f/cffi-2.1.0-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.whl", hash = "sha256:4d433a51f1870e43a13b6732f92aaf540ff77c2015097c78556f75a2d6c030e0", size = 218760, upload-time = "2026-07-06T21:32:17.98Z" },
-    { url = "https://files.pythonhosted.org/packages/d0/9a/bb1d5ed9c3fcae158e9f6391bf309c95d98c2ac37ed56573228471d0af5e/cffi-2.1.0-cp310-cp310-musllinux_1_2_aarch64.whl", hash = "sha256:3d7f118b5adbfdfead90c25822690b02bc8074fba949bb7858bec4ebd55adb43", size = 221230, upload-time = "2026-07-06T21:32:19.407Z" },
-    { url = "https://files.pythonhosted.org/packages/41/aa/3c1409cdd26094efacd1c36c66e0a6eb9d4296e4fd4f9901b8b2042f4323/cffi-2.1.0-cp310-cp310-musllinux_1_2_i686.whl", hash = "sha256:c5f5df567f6eb216de69be06ce55c8b714090fae02b18a3b40da8163b8c5fa9c", size = 213524, upload-time = "2026-07-06T21:32:20.828Z" },
-    { url = "https://files.pythonhosted.org/packages/fa/75/74dfb7c3fc6ebbd408038476bd4c1d7e925c62614e7b9c534ecc34218288/cffi-2.1.0-cp310-cp310-musllinux_1_2_x86_64.whl", hash = "sha256:11b3fb55f4f8ad92274ed26705f65d8f91457de71f5380061eb6d125a768fecd", size = 220341, upload-time = "2026-07-06T21:32:21.9Z" },
-    { url = "https://files.pythonhosted.org/packages/70/b6/9003c33a3e7d2c1306f5962e646457dcfe5a8cd8fce6bbe02d7af25db783/cffi-2.1.0-cp310-cp310-win32.whl", hash = "sha256:9d72af0cf10a76a600a9690078fe31c63b9588c8e86bf9fd353f713c84b5db0f", size = 174578, upload-time = "2026-07-06T21:32:23.073Z" },
-    { url = "https://files.pythonhosted.org/packages/8a/26/710688310447531c7a22f857c7f79d9855ec18b03e04494ced723fb37e2f/cffi-2.1.0-cp310-cp310-win_amd64.whl", hash = "sha256:fb62edb5bb52cca65fab91a63afa7561607120d26090a7e8fda6fb9f064726da", size = 185071, upload-time = "2026-07-06T21:32:24.671Z" },
     { url = "https://files.pythonhosted.org/packages/d3/67/85c89a59ba36a671e79638f44d466749f08179266a57e4f2ffdf92174072/cffi-2.1.0-cp311-cp311-macosx_10_15_x86_64.whl", hash = "sha256:02cb7ff33ded4f1532476731f89ede53e2e488a8e6205515a82144246ffa7dcc", size = 183845, upload-time = "2026-07-06T21:32:26.32Z" },
     { url = "https://files.pythonhosted.org/packages/ea/dd/e3b0baa2d3d6a857ac72b7efbf18e32e487c9cdafcc13049ad765495b15e/cffi-2.1.0-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:f5bce581e6b8c235e566a14768a943b172ada3ed73537bb0c0be1edee312d4e7", size = 184186, upload-time = "2026-07-06T21:32:28.025Z" },
     { url = "https://files.pythonhosted.org/packages/65/68/9f3ef890cf3c6ab97bd531c5677f67613d302165d16f8142b2811782a614/cffi-2.1.0-cp311-cp311-manylinux1_i686.manylinux2014_i686.manylinux_2_17_i686.manylinux_2_5_i686.whl", hash = "sha256:30b65779d598c370374fefabf138d456fd6f3216bfa7bedfab1ba82025b0cd93", size = 211892, upload-time = "2026-07-06T21:32:29.565Z" },
@@ -245,19 +228,6 @@ version = "3.4.9"
 source = { registry = "https://pypi.org/simple" }
 sdist = { url = "https://files.pythonhosted.org/packages/bd/2a/23f34ec9d04624958e137efdc394888716353190e75f25dd22c7a2c7a8aa/charset_normalizer-3.4.9.tar.gz", hash = "sha256:673611bbd43f0810bec0b0f028ddeaaa501190339cac411f347ac76917c3ae7b", size = 152439, upload-time = "2026-07-07T14:34:58.454Z" }
 wheels = [
-    { url = "https://files.pythonhosted.org/packages/ad/81/8e983840c6e5b93b33c2ba81aa3d52c2e42f0e9a690ce7607a2e61da4a5c/charset_normalizer-3.4.9-cp310-cp310-macosx_10_9_universal2.whl", hash = "sha256:cd6280cf040f233bd7d3407b743b4b4c74f70e8e1c4199cb112a62c941c0772a", size = 322240, upload-time = "2026-07-07T14:32:36.236Z" },
-    { url = "https://files.pythonhosted.org/packages/de/d1/b4319dc3229d8272fba305e206fc0a148e2de8d4087917ce62ae6382f359/charset_normalizer-3.4.9-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:aa99adc8f081b475a12843953db36831eaf83ec33eb46a90629ca6a5de45a616", size = 216475, upload-time = "2026-07-07T14:32:38.142Z" },
-    { url = "https://files.pythonhosted.org/packages/80/33/6c99c1b3e6b8bf730e1bc809b9a2608f224145069114c479a2e9e1494346/charset_normalizer-3.4.9-cp310-cp310-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl", hash = "sha256:c1225416b463483160e4af85d5fc3a9690ccb53fd4b1865a6437825f5ede3209", size = 238670, upload-time = "2026-07-07T14:32:39.658Z" },
-    { url = "https://files.pythonhosted.org/packages/7f/f4/ffbb83546e1f198ecc70ecd372b65cf2b50f9068b380abd67640f17a8e18/charset_normalizer-3.4.9-cp310-cp310-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl", hash = "sha256:16d10d789dd9bcca1173c95af82c58433122564b7bc39385124be735a35cbe99", size = 233476, upload-time = "2026-07-07T14:32:41.155Z" },
-    { url = "https://files.pythonhosted.org/packages/e8/5f/b98b8da398637b551e427e7be922bdec19177dc54d6811dcdaa503f23aac/charset_normalizer-3.4.9-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:9bb41182d93ea91f60b4bc8fbf4c820c69ef8a12ab2d917f3f1834f1acad07e8", size = 223817, upload-time = "2026-07-07T14:32:42.592Z" },
-    { url = "https://files.pythonhosted.org/packages/36/31/a276bb2e66243072a3fd06fdcab9cbb61a305b02143d70d2bda21d888fa8/charset_normalizer-3.4.9-cp310-cp310-manylinux_2_31_armv7l.whl", hash = "sha256:bcf74c1df76758a395bf0af608c04c82257523f55c9868b334f06270d0f2112b", size = 207974, upload-time = "2026-07-07T14:32:44.258Z" },
-    { url = "https://files.pythonhosted.org/packages/5e/be/7ee4453d7e88dfbc4104ccd34900b9f2c7c17dac22881865fe0e82424a25/charset_normalizer-3.4.9-cp310-cp310-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl", hash = "sha256:b5314963fce9b0b12743891de876e724997864ee22aa496f903f426c7e2fa5b2", size = 221655, upload-time = "2026-07-07T14:32:45.64Z" },
-    { url = "https://files.pythonhosted.org/packages/1d/85/181c652953eb5276d198f375b1dd641047392050098100a3a02d6534f657/charset_normalizer-3.4.9-cp310-cp310-musllinux_1_2_aarch64.whl", hash = "sha256:e9701d0049d92c16703a42771b98d560b95248949f23f8cf7b4eddd201814fb9", size = 219229, upload-time = "2026-07-07T14:32:47.376Z" },
-    { url = "https://files.pythonhosted.org/packages/0c/e7/aaf6da33fc9f4691cda8f7efbc9f69179d3d39ec8a4799baf273ee1d8db0/charset_normalizer-3.4.9-cp310-cp310-musllinux_1_2_armv7l.whl", hash = "sha256:65a7ff3f705e57d392f7261b6d0550fe137c3019477431f1c355e0db0a7d3e15", size = 209704, upload-time = "2026-07-07T14:32:48.855Z" },
-    { url = "https://files.pythonhosted.org/packages/63/01/f2fb3bd3a73be48b173ee0c6aa8d2497af97d5663a8c4c4b491de4c62f7a/charset_normalizer-3.4.9-cp310-cp310-musllinux_1_2_x86_64.whl", hash = "sha256:79580094b00d1789d1f93ea55bc43cb2f611910c72235b7657f3482ddcc1b22d", size = 226243, upload-time = "2026-07-07T14:32:50.239Z" },
-    { url = "https://files.pythonhosted.org/packages/c4/02/c57a22739fe05246b0b5783b3bfb6afaac4eebb46f3ececdfb2f048f780e/charset_normalizer-3.4.9-cp310-cp310-win32.whl", hash = "sha256:432786d3561e69aeeae6c7e8648964ce0ad05736120135601f87ac26b9c83381", size = 150935, upload-time = "2026-07-07T14:32:51.676Z" },
-    { url = "https://files.pythonhosted.org/packages/37/8d/ca39a7559a4797505530d084fd3a49a2c959efbbbff146302fb7be4e3b35/charset_normalizer-3.4.9-cp310-cp310-win_amd64.whl", hash = "sha256:8c041122946b7ba21bb32c45b1aa57b1be35527690aeb3c5c234521085632eee", size = 162314, upload-time = "2026-07-07T14:32:53.193Z" },
-    { url = "https://files.pythonhosted.org/packages/01/da/a44bd7a13d426e69e4894557106cd58669097bfad4a8681123b618fbfc5d/charset_normalizer-3.4.9-cp310-cp310-win_arm64.whl", hash = "sha256:375b83ed0aecfce76c16d198fbc21f3b11b337d68662bea0a995046682a11419", size = 153075, upload-time = "2026-07-07T14:32:54.554Z" },
     { url = "https://files.pythonhosted.org/packages/0b/e3/85ec501f206fb049259288c1f3506e53876937fb00edb47009348e66756b/charset_normalizer-3.4.9-cp311-cp311-macosx_10_9_universal2.whl", hash = "sha256:0e94703ec9684807f20cfb5eed95c70f67f2a8f21ad620146d7b5a13677b93e5", size = 317075, upload-time = "2026-07-07T14:32:56.021Z" },
     { url = "https://files.pythonhosted.org/packages/c3/69/2a5385192e67175f7d8bd5ce4f57c24bc956439adeae5c13a99aa28a53d1/charset_normalizer-3.4.9-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:2a441ea71902098ffe78c5abe6c494f44160b4af614ed16c3d9a3b1d17fd8ee2", size = 213837, upload-time = "2026-07-07T14:32:57.78Z" },
     { url = "https://files.pythonhosted.org/packages/b3/46/03ddc7da576d814fe0a36dd1f0fd3258e95404b4b2e3c026b7923d7e133f/charset_normalizer-3.4.9-cp311-cp311-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl", hash = "sha256:304b13570067b2547562e308af560b3963857b1fa90bd6afd978130130fe2d6a", size = 235503, upload-time = "2026-07-07T14:32:59.205Z" },
@@ -353,7 +323,6 @@ version = "49.0.0"
 source = { registry = "https://pypi.org/simple" }
 dependencies = [
     { name = "cffi", marker = "platform_python_implementation != 'PyPy'" },
-    { name = "typing-extensions", marker = "python_full_version < '3.11'" },
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/1f/99/d1c90d6041656cc6ee229dc99cd67fd0cd5aec3c5f7d72fffc27cc750054/cryptography-49.0.0.tar.gz", hash = "sha256:f89660a348f4f78a92366240a61404e337586ef7f5909a2fef59ca88ef505493", size = 854345, upload-time = "2026-06-12T20:02:30.512Z" }
 wheels = [
@@ -422,18 +391,6 @@ wheels = [
     { url = "https://files.pythonhosted.org/packages/8f/d7/9322c609343d929e75e7e5e6255e614fcc67572cfd083959cdef3b7aad79/docutils-0.21.2-py3-none-any.whl", hash = "sha256:dafca5b9e384f0e419294eb4d2ff9fa826435bf15f15b7bd45723e8ad76811b2", size = 587408, upload-time = "2024-04-23T18:57:14.835Z" },
 ]
 
-[[package]]
-name = "exceptiongroup"
-version = "1.3.1"
-source = { registry = "https://pypi.org/simple" }
-dependencies = [
-    { name = "typing-extensions", marker = "python_full_version < '3.11'" },
-]
-sdist = { url = "https://files.pythonhosted.org/packages/50/79/66800aadf48771f6b62f7eb014e352e5d06856655206165d775e675a02c9/exceptiongroup-1.3.1.tar.gz", hash = "sha256:8b412432c6055b0b7d14c310000ae93352ed6754f70fa8f7c34141f91c4e3219", size = 30371, upload-time = "2025-11-21T23:01:54.787Z" }
-wheels = [
-    { url = "https://files.pythonhosted.org/packages/8a/0e/97c33bf5009bdbac74fd2beace167cab3f978feb69cc36f1ef79360d6c4e/exceptiongroup-1.3.1-py3-none-any.whl", hash = "sha256:a7a39a3bd276781e98394987d3a5701d0c4edffb633bb7a5144577f82c773598", size = 16740, upload-time = "2025-11-21T23:01:53.443Z" },
-]
-
 [[package]]
 name = "filelock"
 version = "3.32.2"
@@ -472,14 +429,12 @@ dev = [
 ]
 docs = [
     { name = "pallets-sphinx-themes" },
-    { name = "sphinx", version = "8.1.3", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version < '3.11'" },
-    { name = "sphinx", version = "8.2.3", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version >= '3.11'" },
+    { name = "sphinx" },
     { name = "sphinx-tabs" },
     { name = "sphinxcontrib-log-cabinet" },
 ]
 docs-auto = [
-    { name = "sphinx-autobuild", version = "2024.10.3", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version < '3.11'" },
-    { name = "sphinx-autobuild", version = "2025.8.25", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version >= '3.11'" },
+    { name = "sphinx-autobuild" },
 ]
 gha-update = [
     { name = "gha-update", marker = "python_full_version >= '3.12'" },
@@ -556,8 +511,8 @@ name = "gha-update"
 version = "0.2.0"
 source = { registry = "https://pypi.org/simple" }
 dependencies = [
-    { name = "click", marker = "python_full_version >= '3.12'" },
-    { name = "httpx", marker = "python_full_version >= '3.12'" },
+    { name = "click" },
+    { name = "httpx" },
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/46/e8/eb710e08998a22b314cc068f14805cfdd12e3934a5496c8916c5a164c65a/gha_update-0.2.0.tar.gz", hash = "sha256:328ee0db09346ad13ee90646698cea2ec1f9035964ddd7c2a728a91034c3f4b0", size = 4756, upload-time = "2025-07-14T03:13:33.254Z" }
 wheels = [
@@ -578,8 +533,8 @@ name = "httpcore"
 version = "1.0.9"
 source = { registry = "https://pypi.org/simple" }
 dependencies = [
-    { name = "certifi", marker = "python_full_version >= '3.12'" },
-    { name = "h11", marker = "python_full_version >= '3.12'" },
+    { name = "certifi" },
+    { name = "h11" },
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/06/94/82699a10bca87a5556c9c59b5963f2d039dbd239f25bc2a63907a05a14cb/httpcore-1.0.9.tar.gz", hash = "sha256:6e34463af53fd2ab5d807f399a9b45ea31c3dfa2276f15a2c3f00afff6e176e8", size = 85484, upload-time = "2025-04-24T22:06:22.219Z" }
 wheels = [
@@ -591,10 +546,10 @@ name = "httpx"
 version = "0.28.1"
 source = { registry = "https://pypi.org/simple" }
 dependencies = [
-    { name = "anyio", marker = "python_full_version >= '3.12'" },
-    { name = "certifi", marker = "python_full_version >= '3.12'" },
-    { name = "httpcore", marker = "python_full_version >= '3.12'" },
-    { name = "idna", marker = "python_full_version >= '3.12'" },
+    { name = "anyio" },
+    { name = "certifi" },
+    { name = "httpcore" },
+    { name = "idna" },
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/b1/df/48c586a5fe32a0f01324ee087459e112ebb7224f646c0b5023f5e79e9956/httpx-0.28.1.tar.gz", hash = "sha256:75e98c5f16b0f35b567856f597f06ff2270a374470a5c2392242528e3e3e42fc", size = 141406, upload-time = "2024-12-06T15:37:23.222Z" }
 wheels = [
@@ -664,18 +619,6 @@ version = "0.13.0"
 source = { registry = "https://pypi.org/simple" }
 sdist = { url = "https://files.pythonhosted.org/packages/dc/2f/3908645ddddab7120b46295e541ead308109fa48dbec7d67d7a778870d60/librt-0.13.0.tar.gz", hash = "sha256:1d2a610c14ac0d0750ee0a3ab8548e83155258387891caaca04def4bf7289781", size = 211402, upload-time = "2026-07-08T12:26:29.834Z" }
 wheels = [
-    { url = "https://files.pythonhosted.org/packages/89/2f/ec5241c38e7fa0fe6c26bfc450e78b9489a6c3c08b394b85d2c10e506975/librt-0.13.0-cp310-cp310-macosx_10_9_x86_64.whl", hash = "sha256:34e47058fcc69a313293d6dee94216a4f30c929ae6f2476e58c5ba635aa639d5", size = 148654, upload-time = "2026-07-08T12:24:30.622Z" },
-    { url = "https://files.pythonhosted.org/packages/a5/1a/d651e18d3ee7aa2879322368c4f278bb7ecaa6b90caadfdec4ebfa8389f3/librt-0.13.0-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:dbdd5b6509d0c2a8fe72cf494c299a61dbd58142a90a4190664ae159e4a7b547", size = 153537, upload-time = "2026-07-08T12:24:31.773Z" },
-    { url = "https://files.pythonhosted.org/packages/45/18/10bff2122577246009d9619b6569596daf69b7648812f997ca9ca0426f60/librt-0.13.0-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:2e56ea4ee4df77585a6b5c138f6538680886024fa559f5b55bd14b12e98e67b2", size = 494336, upload-time = "2026-07-08T12:24:33.079Z" },
-    { url = "https://files.pythonhosted.org/packages/67/69/87dfee871b852970f137fdeae8e2ca356c5ab38e6f21d2a3299535fc3159/librt-0.13.0-cp310-cp310-manylinux2014_i686.manylinux_2_17_i686.manylinux_2_28_i686.whl", hash = "sha256:f1f9cc4d09a46d9cb3c2063ae100629d3f52a6517c3c08c2f4c9828261883929", size = 485393, upload-time = "2026-07-08T12:24:34.324Z" },
-    { url = "https://files.pythonhosted.org/packages/e9/d5/625447a8c0441ff5f15f4ac5e1d323fb9d4d256ebfde7a3c8e003f646057/librt-0.13.0-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:f125f5d46b20f89dc5587a55cc416b4ba2a5b2ffda36d048ee120e17598a653a", size = 515382, upload-time = "2026-07-08T12:24:35.575Z" },
-    { url = "https://files.pythonhosted.org/packages/8d/d8/1c8c49ea04235960426444deece9092a6b3a9587a850a81bae2335317411/librt-0.13.0-cp310-cp310-manylinux_2_34_riscv64.manylinux_2_39_riscv64.whl", hash = "sha256:2608d3b39f9e0b4a66a130d9150c615cba40a5090d25eeeaa225e0e46de8c0ac", size = 509483, upload-time = "2026-07-08T12:24:36.923Z" },
-    { url = "https://files.pythonhosted.org/packages/6f/65/f1760fc48050e215201a03506c32b7270159088d01f64557b53e39e74a45/librt-0.13.0-cp310-cp310-musllinux_1_2_aarch64.whl", hash = "sha256:9fd35e95ab5e45c3901d37110263c7db85a961110f5460588fe37f8c131f88a7", size = 532503, upload-time = "2026-07-08T12:24:38.203Z" },
-    { url = "https://files.pythonhosted.org/packages/18/1b/793e281dcf494879eff99f642b63ebc9c7c58694a1c2d1e93362a22c7041/librt-0.13.0-cp310-cp310-musllinux_1_2_i686.whl", hash = "sha256:5f31b0aa13c9b04370d4da6be1ab7779776b3a075cceb6747a39a4be85fe1e40", size = 537027, upload-time = "2026-07-08T12:24:39.34Z" },
-    { url = "https://files.pythonhosted.org/packages/69/45/0801bbb40c9eea795d3dd3ce91c4c5f3fe7d42d23ec4be3e8cb283bcc754/librt-0.13.0-cp310-cp310-musllinux_1_2_riscv64.whl", hash = "sha256:0b795f5fc70fbbb787ceaf79bb3a0d627bcc33c53de51741755263ec406b775a", size = 517100, upload-time = "2026-07-08T12:24:40.907Z" },
-    { url = "https://files.pythonhosted.org/packages/a1/6c/eb5f514f8e29d4924bc0ff4601dd7b4175557e182e7c0721e84cffa39b8a/librt-0.13.0-cp310-cp310-musllinux_1_2_x86_64.whl", hash = "sha256:36b306a623aaad96fe4b378692b54f9c0789fccd833b9851753d5fbf6138cfde", size = 558653, upload-time = "2026-07-08T12:24:42.359Z" },
-    { url = "https://files.pythonhosted.org/packages/b4/bf/f140100d1b59fe87ff40b5ecbb4e27924335b189a784e230ee465452f6c2/librt-0.13.0-cp310-cp310-win32.whl", hash = "sha256:a3762e75fcac8c9e4dacaaf438bffd9003e2ca2c531b756f3c0035deefa674c8", size = 104402, upload-time = "2026-07-08T12:24:43.668Z" },
-    { url = "https://files.pythonhosted.org/packages/22/7c/57e40fef7cfb61869341cb28bdcefe8a950bebcbecca74a397bae14dce4a/librt-0.13.0-cp310-cp310-win_amd64.whl", hash = "sha256:d63bae12a8aeb51380be3438e4dc4bd27354d0f8e19166b2f44e3e94d6f552dc", size = 125002, upload-time = "2026-07-08T12:24:44.793Z" },
     { url = "https://files.pythonhosted.org/packages/89/25/a6498964cfeec270c468cffdc118f69c29b412593610d55fa1327ca51ff4/librt-0.13.0-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:1b5a7bbff495baedbd9b916c367d66854008f8f3b575908ded477c499dc60082", size = 148029, upload-time = "2026-07-08T12:24:45.961Z" },
     { url = "https://files.pythonhosted.org/packages/78/59/dc86d1bffd8e0c2818bace29d9f7783cfbb8e0673bf3673b5bbd5bbe0420/librt-0.13.0-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:34bc7938b9fdf14fe32a406c19c71faf894c5cee7e7474bd0be2f17200b82d14", size = 153036, upload-time = "2026-07-08T12:24:47.257Z" },
     { url = "https://files.pythonhosted.org/packages/29/3f/b923826660f02f286186cd9303d52bb05ced0a13708edc104dc8480920e3/librt-0.13.0-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:f40e56b61b41be5f7dec938cfeffd660668cf4b5e72c78e7bd671d66b7bc2c79", size = 493062, upload-time = "2026-07-08T12:24:48.483Z" },
@@ -751,17 +694,6 @@ version = "3.0.3"
 source = { registry = "https://pypi.org/simple" }
 sdist = { url = "https://files.pythonhosted.org/packages/7e/99/7690b6d4034fffd95959cbe0c02de8deb3098cc577c67bb6a24fe5d7caa7/markupsafe-3.0.3.tar.gz", hash = "sha256:722695808f4b6457b320fdc131280796bdceb04ab50fe1795cd540799ebe1698", size = 80313, upload-time = "2025-09-27T18:37:40.426Z" }
 wheels = [
-    { url = "https://files.pythonhosted.org/packages/e8/4b/3541d44f3937ba468b75da9eebcae497dcf67adb65caa16760b0a6807ebb/markupsafe-3.0.3-cp310-cp310-macosx_10_9_x86_64.whl", hash = "sha256:2f981d352f04553a7171b8e44369f2af4055f888dfb147d55e42d29e29e74559", size = 11631, upload-time = "2025-09-27T18:36:05.558Z" },
-    { url = "https://files.pythonhosted.org/packages/98/1b/fbd8eed11021cabd9226c37342fa6ca4e8a98d8188a8d9b66740494960e4/markupsafe-3.0.3-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:e1c1493fb6e50ab01d20a22826e57520f1284df32f2d8601fdd90b6304601419", size = 12057, upload-time = "2025-09-27T18:36:07.165Z" },
-    { url = "https://files.pythonhosted.org/packages/40/01/e560d658dc0bb8ab762670ece35281dec7b6c1b33f5fbc09ebb57a185519/markupsafe-3.0.3-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:1ba88449deb3de88bd40044603fafffb7bc2b055d626a330323a9ed736661695", size = 22050, upload-time = "2025-09-27T18:36:08.005Z" },
-    { url = "https://files.pythonhosted.org/packages/af/cd/ce6e848bbf2c32314c9b237839119c5a564a59725b53157c856e90937b7a/markupsafe-3.0.3-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:f42d0984e947b8adf7dd6dde396e720934d12c506ce84eea8476409563607591", size = 20681, upload-time = "2025-09-27T18:36:08.881Z" },
-    { url = "https://files.pythonhosted.org/packages/c9/2a/b5c12c809f1c3045c4d580b035a743d12fcde53cf685dbc44660826308da/markupsafe-3.0.3-cp310-cp310-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl", hash = "sha256:c0c0b3ade1c0b13b936d7970b1d37a57acde9199dc2aecc4c336773e1d86049c", size = 20705, upload-time = "2025-09-27T18:36:10.131Z" },
-    { url = "https://files.pythonhosted.org/packages/cf/e3/9427a68c82728d0a88c50f890d0fc072a1484de2f3ac1ad0bfc1a7214fd5/markupsafe-3.0.3-cp310-cp310-musllinux_1_2_aarch64.whl", hash = "sha256:0303439a41979d9e74d18ff5e2dd8c43ed6c6001fd40e5bf2e43f7bd9bbc523f", size = 21524, upload-time = "2025-09-27T18:36:11.324Z" },
-    { url = "https://files.pythonhosted.org/packages/bc/36/23578f29e9e582a4d0278e009b38081dbe363c5e7165113fad546918a232/markupsafe-3.0.3-cp310-cp310-musllinux_1_2_riscv64.whl", hash = "sha256:d2ee202e79d8ed691ceebae8e0486bd9a2cd4794cec4824e1c99b6f5009502f6", size = 20282, upload-time = "2025-09-27T18:36:12.573Z" },
-    { url = "https://files.pythonhosted.org/packages/56/21/dca11354e756ebd03e036bd8ad58d6d7168c80ce1fe5e75218e4945cbab7/markupsafe-3.0.3-cp310-cp310-musllinux_1_2_x86_64.whl", hash = "sha256:177b5253b2834fe3678cb4a5f0059808258584c559193998be2601324fdeafb1", size = 20745, upload-time = "2025-09-27T18:36:13.504Z" },
-    { url = "https://files.pythonhosted.org/packages/87/99/faba9369a7ad6e4d10b6a5fbf71fa2a188fe4a593b15f0963b73859a1bbd/markupsafe-3.0.3-cp310-cp310-win32.whl", hash = "sha256:2a15a08b17dd94c53a1da0438822d70ebcd13f8c3a95abe3a9ef9f11a94830aa", size = 14571, upload-time = "2025-09-27T18:36:14.779Z" },
-    { url = "https://files.pythonhosted.org/packages/d6/25/55dc3ab959917602c96985cb1253efaa4ff42f71194bddeb61eb7278b8be/markupsafe-3.0.3-cp310-cp310-win_amd64.whl", hash = "sha256:c4ffb7ebf07cfe8931028e3e4c85f0357459a3f9f9490886198848f4fa002ec8", size = 15056, upload-time = "2025-09-27T18:36:16.125Z" },
-    { url = "https://files.pythonhosted.org/packages/d0/9e/0a02226640c255d1da0b8d12e24ac2aa6734da68bff14c05dd53b94a0fc3/markupsafe-3.0.3-cp310-cp310-win_arm64.whl", hash = "sha256:e2103a929dfa2fcaf9bb4e7c091983a49c9ac3b19c9061b6d5427dd7d14d81a1", size = 13932, upload-time = "2025-09-27T18:36:17.311Z" },
     { url = "https://files.pythonhosted.org/packages/08/db/fefacb2136439fc8dd20e797950e749aa1f4997ed584c62cfb8ef7c2be0e/markupsafe-3.0.3-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:1cc7ea17a6824959616c525620e387f6dd30fec8cb44f649e31712db02123dad", size = 11631, upload-time = "2025-09-27T18:36:18.185Z" },
     { url = "https://files.pythonhosted.org/packages/e1/2e/5898933336b61975ce9dc04decbc0a7f2fee78c30353c5efba7f2d6ff27a/markupsafe-3.0.3-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:4bd4cd07944443f5a265608cc6aab442e4f74dff8088b0dfc8238647b8f6ae9a", size = 12058, upload-time = "2025-09-27T18:36:19.444Z" },
     { url = "https://files.pythonhosted.org/packages/1d/09/adf2df3699d87d1d8184038df46a9c80d78c0148492323f4693df54e17bb/markupsafe-3.0.3-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:6b5420a1d9450023228968e7e6a9ce57f65d148ab56d2313fcd589eee96a7a50", size = 24287, upload-time = "2025-09-27T18:36:20.768Z" },
@@ -839,18 +771,10 @@ dependencies = [
     { name = "librt", marker = "platform_python_implementation != 'PyPy'" },
     { name = "mypy-extensions" },
     { name = "pathspec" },
-    { name = "tomli", marker = "python_full_version < '3.11'" },
     { name = "typing-extensions" },
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/12/af/4e516a05d3ca2eb9283e9ec45b2c02225c1514dd6da49fd3c9eaa6639370/mypy-2.3.0.tar.gz", hash = "sha256:465965d41cd9a2726694e983e8ce7113259327bec798115d1e1dfa2a52fb666e", size = 3988104, upload-time = "2026-07-13T11:34:53.387Z" }
 wheels = [
-    { url = "https://files.pythonhosted.org/packages/a9/09/f2f5f45dae0c9a0891e4751a73312730e009395102e5d72a22a976cca41f/mypy-2.3.0-cp310-cp310-macosx_10_9_x86_64.whl", hash = "sha256:1fa8d916ac3b705af733c4c1e6c9ebe38fd0d52beb15b105c3e8355b55e6ecdc", size = 14927774, upload-time = "2026-07-13T11:28:38.224Z" },
-    { url = "https://files.pythonhosted.org/packages/56/b9/345367effd3a6877275a94d481614bfca983f45e028c6290e2cc54603811/mypy-2.3.0-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:28e1e2af8cd8fff551fd30f2fe4b03fb76764ac8b1ba6c6a1bd00ad32b412db3", size = 14000127, upload-time = "2026-07-13T11:30:19.57Z" },
-    { url = "https://files.pythonhosted.org/packages/99/6c/a10b7a7b9f0a755fb94e27ae834d4cea9ad6c5221f9325eef8f182641feb/mypy-2.3.0-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:3e77244df3843048c3f927182916730e40c124cbaa43905c1fb86cb382aa0805", size = 14229437, upload-time = "2026-07-13T11:28:17.765Z" },
-    { url = "https://files.pythonhosted.org/packages/d9/bd/a26a602acb1bbf849fa4bdac4bc657ee2f11c0c2a764a2cc87a5304e865c/mypy-2.3.0-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:9559ab18a9c9957dfa3004ab57cd4bac5f26a724329a9584e583367f0c2e1117", size = 15171457, upload-time = "2026-07-13T11:29:01.834Z" },
-    { url = "https://files.pythonhosted.org/packages/7f/14/124f462bef69bcbc90b9358088460b6091954a3e004852fcd9948db617a5/mypy-2.3.0-cp310-cp310-musllinux_1_2_x86_64.whl", hash = "sha256:09abd66d8685e73f8f7d17b847c3e104d9a7b164a8706ea87d6c96a3d45816d5", size = 15478281, upload-time = "2026-07-13T11:32:23.413Z" },
-    { url = "https://files.pythonhosted.org/packages/db/a4/8bdca6a8ac8d856d82ed049144af2721245a135c2e8001d3890c93975852/mypy-2.3.0-cp310-cp310-win_amd64.whl", hash = "sha256:5e91adad1ca81742ac7ef9893959911df867752206b37135185e88dfb3c89494", size = 11148008, upload-time = "2026-07-13T11:34:17.332Z" },
-    { url = "https://files.pythonhosted.org/packages/83/41/490eea348e60ba50decec20bc750605444149a5d7a8cc560042f90ba2c75/mypy-2.3.0-cp310-cp310-win_arm64.whl", hash = "sha256:6f99ec626e3c3a2f7c0b22c5b90ddb5dabb1c18729c971e9bdaca1f1766d2cee", size = 10142329, upload-time = "2026-07-13T11:32:52.116Z" },
     { url = "https://files.pythonhosted.org/packages/e6/b9/d75b3082b05f1b3028828aeb18e74ae5ab0a0936051bbf1f32f59f654747/mypy-2.3.0-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:3419d00717afbc5265b50dd14b1278f29ea4884dd398ab67873489ac093fd329", size = 14838725, upload-time = "2026-07-13T11:32:44.655Z" },
     { url = "https://files.pythonhosted.org/packages/a9/50/79a65c6ea6e115bc73296038a4543b2d5c91f07912b918a2c616a2514bba/mypy-2.3.0-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:cfca8ee88544090f86b6dcce05ec55d66eb48a762412ac2507810ba4bd793b6f", size = 13911128, upload-time = "2026-07-13T11:32:02.021Z" },
     { url = "https://files.pythonhosted.org/packages/90/48/e11ed7716c26953ca321f726e452e374dbf81a6f2b8b212ec02af29b6b8f/mypy-2.3.0-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:75cbb4b9ef04a0c84a957f07abc4504fbf64b8dcc145675101f2d3a78a4b1d6a", size = 14146742, upload-time = "2026-07-13T11:33:03.313Z" },
@@ -923,8 +847,7 @@ version = "2.5.0"
 source = { registry = "https://pypi.org/simple" }
 dependencies = [
     { name = "packaging" },
-    { name = "sphinx", version = "8.1.3", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version < '3.11'" },
-    { name = "sphinx", version = "8.2.3", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version >= '3.11'" },
+    { name = "sphinx" },
     { name = "sphinx-notfound-page" },
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/74/60/1ee4b7dfce36150cea485b6d47358d58e59e96e8c5bdadee8030d483ce38/pallets_sphinx_themes-2.5.0.tar.gz", hash = "sha256:ef8609704b80e8a5d508a88adeb0559234311a1cf3362427aca9d283b22c80ef", size = 216582, upload-time = "2026-02-25T16:28:22.83Z" }
@@ -1012,7 +935,6 @@ version = "1.11.0"
 source = { registry = "https://pypi.org/simple" }
 dependencies = [
     { name = "packaging" },
-    { name = "tomli", marker = "python_full_version < '3.11'" },
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/ab/bd/2f985c12bf33fdd8637e3a8f9418d6806f177601dee7c4924d0b2bb28650/pyproject_api-1.11.0.tar.gz", hash = "sha256:b8807d85a293e6c9f133e6575946fed45f1d42b22d58c780b33aa2421a799549", size = 23787, upload-time = "2026-07-21T13:09:33.744Z" }
 wheels = [
@@ -1038,12 +960,10 @@ version = "9.1.1"
 source = { registry = "https://pypi.org/simple" }
 dependencies = [
     { name = "colorama", marker = "sys_platform == 'win32'" },
-    { name = "exceptiongroup", marker = "python_full_version < '3.11'" },
     { name = "iniconfig" },
     { name = "packaging" },
     { name = "pluggy" },
     { name = "pygments" },
-    { name = "tomli", marker = "python_full_version < '3.11'" },
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/e4/47/b9efed96c114afcfa3c9d3fe98a76a1d14c74a9e266d397cf6eb64be5e01/pytest-9.1.1.tar.gz", hash = "sha256:1088fbde8f2b49d95a549a195707afa7a76a3ce9bcadc26b6d71f0ffda5fe313", size = 1636369, upload-time = "2026-06-19T10:58:32.857Z" }
 wheels = [
@@ -1078,15 +998,6 @@ version = "6.0.3"
 source = { registry = "https://pypi.org/simple" }
 sdist = { url = "https://files.pythonhosted.org/packages/05/8e/961c0007c59b8dd7729d542c61a4d537767a59645b82a0b521206e1e25c2/pyyaml-6.0.3.tar.gz", hash = "sha256:d76623373421df22fb4cf8817020cbb7ef15c725b9d5e45f17e189bfc384190f", size = 130960, upload-time = "2025-09-25T21:33:16.546Z" }
 wheels = [
-    { url = "https://files.pythonhosted.org/packages/f4/a0/39350dd17dd6d6c6507025c0e53aef67a9293a6d37d3511f23ea510d5800/pyyaml-6.0.3-cp310-cp310-macosx_10_13_x86_64.whl", hash = "sha256:214ed4befebe12df36bcc8bc2b64b396ca31be9304b8f59e25c11cf94a4c033b", size = 184227, upload-time = "2025-09-25T21:31:46.04Z" },
-    { url = "https://files.pythonhosted.org/packages/05/14/52d505b5c59ce73244f59c7a50ecf47093ce4765f116cdb98286a71eeca2/pyyaml-6.0.3-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:02ea2dfa234451bbb8772601d7b8e426c2bfa197136796224e50e35a78777956", size = 174019, upload-time = "2025-09-25T21:31:47.706Z" },
-    { url = "https://files.pythonhosted.org/packages/43/f7/0e6a5ae5599c838c696adb4e6330a59f463265bfa1e116cfd1fbb0abaaae/pyyaml-6.0.3-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:b30236e45cf30d2b8e7b3e85881719e98507abed1011bf463a8fa23e9c3e98a8", size = 740646, upload-time = "2025-09-25T21:31:49.21Z" },
-    { url = "https://files.pythonhosted.org/packages/2f/3a/61b9db1d28f00f8fd0ae760459a5c4bf1b941baf714e207b6eb0657d2578/pyyaml-6.0.3-cp310-cp310-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl", hash = "sha256:66291b10affd76d76f54fad28e22e51719ef9ba22b29e1d7d03d6777a9174198", size = 840793, upload-time = "2025-09-25T21:31:50.735Z" },
-    { url = "https://files.pythonhosted.org/packages/7a/1e/7acc4f0e74c4b3d9531e24739e0ab832a5edf40e64fbae1a9c01941cabd7/pyyaml-6.0.3-cp310-cp310-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:9c7708761fccb9397fe64bbc0395abcae8c4bf7b0eac081e12b809bf47700d0b", size = 770293, upload-time = "2025-09-25T21:31:51.828Z" },
-    { url = "https://files.pythonhosted.org/packages/8b/ef/abd085f06853af0cd59fa5f913d61a8eab65d7639ff2a658d18a25d6a89d/pyyaml-6.0.3-cp310-cp310-musllinux_1_2_aarch64.whl", hash = "sha256:418cf3f2111bc80e0933b2cd8cd04f286338bb88bdc7bc8e6dd775ebde60b5e0", size = 732872, upload-time = "2025-09-25T21:31:53.282Z" },
-    { url = "https://files.pythonhosted.org/packages/1f/15/2bc9c8faf6450a8b3c9fc5448ed869c599c0a74ba2669772b1f3a0040180/pyyaml-6.0.3-cp310-cp310-musllinux_1_2_x86_64.whl", hash = "sha256:5e0b74767e5f8c593e8c9b5912019159ed0533c70051e9cce3e8b6aa699fcd69", size = 758828, upload-time = "2025-09-25T21:31:54.807Z" },
-    { url = "https://files.pythonhosted.org/packages/a3/00/531e92e88c00f4333ce359e50c19b8d1de9fe8d581b1534e35ccfbc5f393/pyyaml-6.0.3-cp310-cp310-win32.whl", hash = "sha256:28c8d926f98f432f88adc23edf2e6d4921ac26fb084b028c733d01868d19007e", size = 142415, upload-time = "2025-09-25T21:31:55.885Z" },
-    { url = "https://files.pythonhosted.org/packages/2a/fa/926c003379b19fca39dd4634818b00dec6c62d87faf628d1394e137354d4/pyyaml-6.0.3-cp310-cp310-win_amd64.whl", hash = "sha256:bdb2c67c6c1390b63c6ff89f210c8fd09d9a1217a465701eac7316313c915e4c", size = 158561, upload-time = "2025-09-25T21:31:57.406Z" },
     { url = "https://files.pythonhosted.org/packages/6d/16/a95b6757765b7b031c9374925bb718d55e0a9ba8a1b6a12d25962ea44347/pyyaml-6.0.3-cp311-cp311-macosx_10_13_x86_64.whl", hash = "sha256:44edc647873928551a01e7a563d7452ccdebee747728c1080d881d68af7b997e", size = 185826, upload-time = "2025-09-25T21:31:58.655Z" },
     { url = "https://files.pythonhosted.org/packages/16/19/13de8e4377ed53079ee996e1ab0a9c33ec2faf808a4647b7b4c0d46dd239/pyyaml-6.0.3-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:652cb6edd41e718550aad172851962662ff2681490a8a711af6a4d288dd96824", size = 175577, upload-time = "2025-09-25T21:32:00.088Z" },
     { url = "https://files.pythonhosted.org/packages/0c/62/d2eb46264d4b157dae1275b573017abec435397aa59cbcdab6fc978a8af4/pyyaml-6.0.3-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:10892704fc220243f5305762e276552a0395f7beb4dbf9b14ec8fd43b57f126c", size = 775556, upload-time = "2025-09-25T21:32:01.31Z" },
@@ -1165,7 +1076,7 @@ name = "roman-numerals-py"
 version = "4.1.0"
 source = { registry = "https://pypi.org/simple" }
 dependencies = [
-    { name = "roman-numerals", marker = "python_full_version >= '3.11'" },
+    { name = "roman-numerals" },
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/cb/b5/de96fca640f4f656eb79bbee0e79aeec52e3e0e359f8a3e6a0d366378b64/roman_numerals_py-4.1.0.tar.gz", hash = "sha256:f5d7b2b4ca52dd855ef7ab8eb3590f428c0b1ea480736ce32b01fef2a5f8daf9", size = 4274, upload-time = "2025-12-17T18:25:41.153Z" }
 wheels = [
@@ -1206,106 +1117,45 @@ wheels = [
     { url = "https://files.pythonhosted.org/packages/4c/07/2ebca9b11fb9be7340a818d8d6f63feaebb146be2c4afbd6061701d6df6e/snowballstemmer-3.1.1-py3-none-any.whl", hash = "sha256:7e207fa178741da09cdee59d3ecec3827ad5f92b1fc5c9ff3755b639f71f5752", size = 104164, upload-time = "2026-06-03T00:56:38.614Z" },
 ]
 
-[[package]]
-name = "sphinx"
-version = "8.1.3"
-source = { registry = "https://pypi.org/simple" }
-resolution-markers = [
-    "python_full_version < '3.11'",
-]
-dependencies = [
-    { name = "alabaster", marker = "python_full_version < '3.11'" },
-    { name = "babel", marker = "python_full_version < '3.11'" },
-    { name = "colorama", marker = "python_full_version < '3.11' and sys_platform == 'win32'" },
-    { name = "docutils", marker = "python_full_version < '3.11'" },
-    { name = "imagesize", marker = "python_full_version < '3.11'" },
-    { name = "jinja2", marker = "python_full_version < '3.11'" },
-    { name = "packaging", marker = "python_full_version < '3.11'" },
-    { name = "pygments", marker = "python_full_version < '3.11'" },
-    { name = "requests", marker = "python_full_version < '3.11'" },
-    { name = "snowballstemmer", marker = "python_full_version < '3.11'" },
-    { name = "sphinxcontrib-applehelp", marker = "python_full_version < '3.11'" },
-    { name = "sphinxcontrib-devhelp", marker = "python_full_version < '3.11'" },
-    { name = "sphinxcontrib-htmlhelp", marker = "python_full_version < '3.11'" },
-    { name = "sphinxcontrib-jsmath", marker = "python_full_version < '3.11'" },
-    { name = "sphinxcontrib-qthelp", marker = "python_full_version < '3.11'" },
-    { name = "sphinxcontrib-serializinghtml", marker = "python_full_version < '3.11'" },
-    { name = "tomli", marker = "python_full_version < '3.11'" },
-]
-sdist = { url = "https://files.pythonhosted.org/packages/6f/6d/be0b61178fe2cdcb67e2a92fc9ebb488e3c51c4f74a36a7824c0adf23425/sphinx-8.1.3.tar.gz", hash = "sha256:43c1911eecb0d3e161ad78611bc905d1ad0e523e4ddc202a58a821773dc4c927", size = 8184611, upload-time = "2024-10-13T20:27:13.93Z" }
-wheels = [
-    { url = "https://files.pythonhosted.org/packages/26/60/1ddff83a56d33aaf6f10ec8ce84b4c007d9368b21008876fceda7e7381ef/sphinx-8.1.3-py3-none-any.whl", hash = "sha256:09719015511837b76bf6e03e42eb7595ac8c2e41eeb9c29c5b755c6b677992a2", size = 3487125, upload-time = "2024-10-13T20:27:10.448Z" },
-]
-
 [[package]]
 name = "sphinx"
 version = "8.2.3"
 source = { registry = "https://pypi.org/simple" }
-resolution-markers = [
-    "python_full_version >= '3.15'",
-    "python_full_version >= '3.12' and python_full_version < '3.15'",
-    "python_full_version == '3.11.*'",
-]
 dependencies = [
-    { name = "alabaster", marker = "python_full_version >= '3.11'" },
-    { name = "babel", marker = "python_full_version >= '3.11'" },
-    { name = "colorama", marker = "python_full_version >= '3.11' and sys_platform == 'win32'" },
-    { name = "docutils", marker = "python_full_version >= '3.11'" },
-    { name = "imagesize", marker = "python_full_version >= '3.11'" },
-    { name = "jinja2", marker = "python_full_version >= '3.11'" },
-    { name = "packaging", marker = "python_full_version >= '3.11'" },
-    { name = "pygments", marker = "python_full_version >= '3.11'" },
-    { name = "requests", marker = "python_full_version >= '3.11'" },
-    { name = "roman-numerals-py", marker = "python_full_version >= '3.11'" },
-    { name = "snowballstemmer", marker = "python_full_version >= '3.11'" },
-    { name = "sphinxcontrib-applehelp", marker = "python_full_version >= '3.11'" },
-    { name = "sphinxcontrib-devhelp", marker = "python_full_version >= '3.11'" },
-    { name = "sphinxcontrib-htmlhelp", marker = "python_full_version >= '3.11'" },
-    { name = "sphinxcontrib-jsmath", marker = "python_full_version >= '3.11'" },
-    { name = "sphinxcontrib-qthelp", marker = "python_full_version >= '3.11'" },
-    { name = "sphinxcontrib-serializinghtml", marker = "python_full_version >= '3.11'" },
+    { name = "alabaster" },
+    { name = "babel" },
+    { name = "colorama", marker = "sys_platform == 'win32'" },
+    { name = "docutils" },
+    { name = "imagesize" },
+    { name = "jinja2" },
+    { name = "packaging" },
+    { name = "pygments" },
+    { name = "requests" },
+    { name = "roman-numerals-py" },
+    { name = "snowballstemmer" },
+    { name = "sphinxcontrib-applehelp" },
+    { name = "sphinxcontrib-devhelp" },
+    { name = "sphinxcontrib-htmlhelp" },
+    { name = "sphinxcontrib-jsmath" },
+    { name = "sphinxcontrib-qthelp" },
+    { name = "sphinxcontrib-serializinghtml" },
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/38/ad/4360e50ed56cb483667b8e6dadf2d3fda62359593faabbe749a27c4eaca6/sphinx-8.2.3.tar.gz", hash = "sha256:398ad29dee7f63a75888314e9424d40f52ce5a6a87ae88e7071e80af296ec348", size = 8321876, upload-time = "2025-03-02T22:31:59.658Z" }
 wheels = [
     { url = "https://files.pythonhosted.org/packages/31/53/136e9eca6e0b9dc0e1962e2c908fbea2e5ac000c2a2fbd9a35797958c48b/sphinx-8.2.3-py3-none-any.whl", hash = "sha256:4405915165f13521d875a8c29c8970800a0141c14cc5416a38feca4ea5d9b9c3", size = 3589741, upload-time = "2025-03-02T22:31:56.836Z" },
 ]
 
-[[package]]
-name = "sphinx-autobuild"
-version = "2024.10.3"
-source = { registry = "https://pypi.org/simple" }
-resolution-markers = [
-    "python_full_version < '3.11'",
-]
-dependencies = [
-    { name = "colorama", marker = "python_full_version < '3.11'" },
-    { name = "sphinx", version = "8.1.3", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version < '3.11'" },
-    { name = "starlette", marker = "python_full_version < '3.11'" },
-    { name = "uvicorn", marker = "python_full_version < '3.11'" },
-    { name = "watchfiles", marker = "python_full_version < '3.11'" },
-    { name = "websockets", version = "16.1.1", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version < '3.11'" },
-]
-sdist = { url = "https://files.pythonhosted.org/packages/a5/2c/155e1de2c1ba96a72e5dba152c509a8b41e047ee5c2def9e9f0d812f8be7/sphinx_autobuild-2024.10.3.tar.gz", hash = "sha256:248150f8f333e825107b6d4b86113ab28fa51750e5f9ae63b59dc339be951fb1", size = 14023, upload-time = "2024-10-02T23:15:30.172Z" }
-wheels = [
-    { url = "https://files.pythonhosted.org/packages/18/c0/eba125db38c84d3c74717008fd3cb5000b68cd7e2cbafd1349c6a38c3d3b/sphinx_autobuild-2024.10.3-py3-none-any.whl", hash = "sha256:158e16c36f9d633e613c9aaf81c19b0fc458ca78b112533b20dafcda430d60fa", size = 11908, upload-time = "2024-10-02T23:15:28.739Z" },
-]
-
 [[package]]
 name = "sphinx-autobuild"
 version = "2025.8.25"
 source = { registry = "https://pypi.org/simple" }
-resolution-markers = [
-    "python_full_version >= '3.15'",
-    "python_full_version >= '3.12' and python_full_version < '3.15'",
-    "python_full_version == '3.11.*'",
-]
 dependencies = [
-    { name = "colorama", marker = "python_full_version >= '3.11'" },
-    { name = "sphinx", version = "8.2.3", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version >= '3.11'" },
-    { name = "starlette", marker = "python_full_version >= '3.11'" },
-    { name = "uvicorn", marker = "python_full_version >= '3.11'" },
-    { name = "watchfiles", marker = "python_full_version >= '3.11'" },
-    { name = "websockets", version = "17.0", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version >= '3.11'" },
+    { name = "colorama" },
+    { name = "sphinx" },
+    { name = "starlette" },
+    { name = "uvicorn" },
+    { name = "watchfiles" },
+    { name = "websockets" },
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/e0/3c/a59a3a453d4133777f7ed2e83c80b7dc817d43c74b74298ca0af869662ad/sphinx_autobuild-2025.8.25.tar.gz", hash = "sha256:9cf5aab32853c8c31af572e4fecdc09c997e2b8be5a07daf2a389e270e85b213", size = 15200, upload-time = "2025-08-25T18:44:55.436Z" }
 wheels = [
@@ -1317,8 +1167,7 @@ name = "sphinx-notfound-page"
 version = "1.1.0"
 source = { registry = "https://pypi.org/simple" }
 dependencies = [
-    { name = "sphinx", version = "8.1.3", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version < '3.11'" },
-    { name = "sphinx", version = "8.2.3", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version >= '3.11'" },
+    { name = "sphinx" },
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/6a/b2/67603444a8ee97b4a8ea71b0a9d6bab1727ed65e362c87e02f818ee57b8a/sphinx_notfound_page-1.1.0.tar.gz", hash = "sha256:913e1754370bb3db201d9300d458a8b8b5fb22e9246a816643a819a9ea2b8067", size = 7392, upload-time = "2025-01-28T18:45:02.871Z" }
 wheels = [
@@ -1332,8 +1181,7 @@ source = { registry = "https://pypi.org/simple" }
 dependencies = [
     { name = "docutils" },
     { name = "pygments" },
-    { name = "sphinx", version = "8.1.3", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version < '3.11'" },
-    { name = "sphinx", version = "8.2.3", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version >= '3.11'" },
+    { name = "sphinx" },
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/ce/30/ca5b0de830f369968d8e3483dd45a8908fd10169c05cd9837f0bd075982e/sphinx_tabs-3.5.0.tar.gz", hash = "sha256:91dba1187e4c35fd37380a56ac228bbd54c6c649b2351829f3bf033718277537", size = 17006, upload-time = "2026-03-03T23:00:30.404Z" }
 wheels = [
@@ -1381,8 +1229,7 @@ name = "sphinxcontrib-log-cabinet"
 version = "1.0.1"
 source = { registry = "https://pypi.org/simple" }
 dependencies = [
-    { name = "sphinx", version = "8.1.3", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version < '3.11'" },
-    { name = "sphinx", version = "8.2.3", source = { registry = "https://pypi.org/simple" }, marker = "python_full_version >= '3.11'" },
+    { name = "sphinx" },
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/75/26/0687391e10c605a4d0c7ebe118c57c51ecc687128bcdae5803d9b96def81/sphinxcontrib-log-cabinet-1.0.1.tar.gz", hash = "sha256:103b2e62df4e57abb943bea05ee9c2beb7da922222c8b77314ffd6ab9901c558", size = 4072, upload-time = "2019-07-05T23:22:34.596Z" }
 wheels = [
@@ -1420,60 +1267,6 @@ wheels = [
     { url = "https://files.pythonhosted.org/packages/ec/bb/2799cc2ede3ed41131f8975621e7213dfc7ef4acbbaadfa440f32500c370/starlette-1.3.1-py3-none-any.whl", hash = "sha256:c7372aae11c3c3f26a42df7bd626cec2f47d03483d261d369516a615a53714c6", size = 73632, upload-time = "2026-06-12T09:23:10.017Z" },
 ]
 
-[[package]]
-name = "tomli"
-version = "2.4.1"
-source = { registry = "https://pypi.org/simple" }
-sdist = { url = "https://files.pythonhosted.org/packages/22/de/48c59722572767841493b26183a0d1cc411d54fd759c5607c4590b6563a6/tomli-2.4.1.tar.gz", hash = "sha256:7c7e1a961a0b2f2472c1ac5b69affa0ae1132c39adcb67aba98568702b9cc23f", size = 17543, upload-time = "2026-03-25T20:22:03.828Z" }
-wheels = [
-    { url = "https://files.pythonhosted.org/packages/f4/11/db3d5885d8528263d8adc260bb2d28ebf1270b96e98f0e0268d32b8d9900/tomli-2.4.1-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:f8f0fc26ec2cc2b965b7a3b87cd19c5c6b8c5e5f436b984e85f486d652285c30", size = 154704, upload-time = "2026-03-25T20:21:10.473Z" },
-    { url = "https://files.pythonhosted.org/packages/6d/f7/675db52c7e46064a9aa928885a9b20f4124ecb9bc2e1ce74c9106648d202/tomli-2.4.1-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:4ab97e64ccda8756376892c53a72bd1f964e519c77236368527f758fbc36a53a", size = 149454, upload-time = "2026-03-25T20:21:12.036Z" },
-    { url = "https://files.pythonhosted.org/packages/61/71/81c50943cf953efa35bce7646caab3cf457a7d8c030b27cfb40d7235f9ee/tomli-2.4.1-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:96481a5786729fd470164b47cdb3e0e58062a496f455ee41b4403be77cb5a076", size = 237561, upload-time = "2026-03-25T20:21:13.098Z" },
-    { url = "https://files.pythonhosted.org/packages/48/c1/f41d9cb618acccca7df82aaf682f9b49013c9397212cb9f53219e3abac37/tomli-2.4.1-cp311-cp311-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:5a881ab208c0baf688221f8cecc5401bd291d67e38a1ac884d6736cbcd8247e9", size = 243824, upload-time = "2026-03-25T20:21:14.569Z" },
-    { url = "https://files.pythonhosted.org/packages/22/e4/5a816ecdd1f8ca51fb756ef684b90f2780afc52fc67f987e3c61d800a46d/tomli-2.4.1-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:47149d5bd38761ac8be13a84864bf0b7b70bc051806bc3669ab1cbc56216b23c", size = 242227, upload-time = "2026-03-25T20:21:15.712Z" },
-    { url = "https://files.pythonhosted.org/packages/6b/49/2b2a0ef529aa6eec245d25f0c703e020a73955ad7edf73e7f54ddc608aa5/tomli-2.4.1-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:ec9bfaf3ad2df51ace80688143a6a4ebc09a248f6ff781a9945e51937008fcbc", size = 247859, upload-time = "2026-03-25T20:21:17.001Z" },
-    { url = "https://files.pythonhosted.org/packages/83/bd/6c1a630eaca337e1e78c5903104f831bda934c426f9231429396ce3c3467/tomli-2.4.1-cp311-cp311-win32.whl", hash = "sha256:ff2983983d34813c1aeb0fa89091e76c3a22889ee83ab27c5eeb45100560c049", size = 97204, upload-time = "2026-03-25T20:21:18.079Z" },
-    { url = "https://files.pythonhosted.org/packages/42/59/71461df1a885647e10b6bb7802d0b8e66480c61f3f43079e0dcd315b3954/tomli-2.4.1-cp311-cp311-win_amd64.whl", hash = "sha256:5ee18d9ebdb417e384b58fe414e8d6af9f4e7a0ae761519fb50f721de398dd4e", size = 108084, upload-time = "2026-03-25T20:21:18.978Z" },
-    { url = "https://files.pythonhosted.org/packages/b8/83/dceca96142499c069475b790e7913b1044c1a4337e700751f48ed723f883/tomli-2.4.1-cp311-cp311-win_arm64.whl", hash = "sha256:c2541745709bad0264b7d4705ad453b76ccd191e64aa6f0fc66b69a293a45ece", size = 95285, upload-time = "2026-03-25T20:21:20.309Z" },
-    { url = "https://files.pythonhosted.org/packages/c1/ba/42f134a3fe2b370f555f44b1d72feebb94debcab01676bf918d0cb70e9aa/tomli-2.4.1-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:c742f741d58a28940ce01d58f0ab2ea3ced8b12402f162f4d534dfe18ba1cd6a", size = 155924, upload-time = "2026-03-25T20:21:21.626Z" },
-    { url = "https://files.pythonhosted.org/packages/dc/c7/62d7a17c26487ade21c5422b646110f2162f1fcc95980ef7f63e73c68f14/tomli-2.4.1-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:7f86fd587c4ed9dd76f318225e7d9b29cfc5a9d43de44e5754db8d1128487085", size = 150018, upload-time = "2026-03-25T20:21:23.002Z" },
-    { url = "https://files.pythonhosted.org/packages/5c/05/79d13d7c15f13bdef410bdd49a6485b1c37d28968314eabee452c22a7fda/tomli-2.4.1-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:ff18e6a727ee0ab0388507b89d1bc6a22b138d1e2fa56d1ad494586d61d2eae9", size = 244948, upload-time = "2026-03-25T20:21:24.04Z" },
-    { url = "https://files.pythonhosted.org/packages/10/90/d62ce007a1c80d0b2c93e02cab211224756240884751b94ca72df8a875ca/tomli-2.4.1-cp312-cp312-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:136443dbd7e1dee43c68ac2694fde36b2849865fa258d39bf822c10e8068eac5", size = 253341, upload-time = "2026-03-25T20:21:25.177Z" },
-    { url = "https://files.pythonhosted.org/packages/1a/7e/caf6496d60152ad4ed09282c1885cca4eea150bfd007da84aea07bcc0a3e/tomli-2.4.1-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:5e262d41726bc187e69af7825504c933b6794dc3fbd5945e41a79bb14c31f585", size = 248159, upload-time = "2026-03-25T20:21:26.364Z" },
-    { url = "https://files.pythonhosted.org/packages/99/e7/c6f69c3120de34bbd882c6fba7975f3d7a746e9218e56ab46a1bc4b42552/tomli-2.4.1-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:5cb41aa38891e073ee49d55fbc7839cfdb2bc0e600add13874d048c94aadddd1", size = 253290, upload-time = "2026-03-25T20:21:27.46Z" },
-    { url = "https://files.pythonhosted.org/packages/d6/2f/4a3c322f22c5c66c4b836ec58211641a4067364f5dcdd7b974b4c5da300c/tomli-2.4.1-cp312-cp312-win32.whl", hash = "sha256:da25dc3563bff5965356133435b757a795a17b17d01dbc0f42fb32447ddfd917", size = 98141, upload-time = "2026-03-25T20:21:28.492Z" },
-    { url = "https://files.pythonhosted.org/packages/24/22/4daacd05391b92c55759d55eaee21e1dfaea86ce5c571f10083360adf534/tomli-2.4.1-cp312-cp312-win_amd64.whl", hash = "sha256:52c8ef851d9a240f11a88c003eacb03c31fc1c9c4ec64a99a0f922b93874fda9", size = 108847, upload-time = "2026-03-25T20:21:29.386Z" },
-    { url = "https://files.pythonhosted.org/packages/68/fd/70e768887666ddd9e9f5d85129e84910f2db2796f9096aa02b721a53098d/tomli-2.4.1-cp312-cp312-win_arm64.whl", hash = "sha256:f758f1b9299d059cc3f6546ae2af89670cb1c4d48ea29c3cacc4fe7de3058257", size = 95088, upload-time = "2026-03-25T20:21:30.677Z" },
-    { url = "https://files.pythonhosted.org/packages/07/06/b823a7e818c756d9a7123ba2cda7d07bc2dd32835648d1a7b7b7a05d848d/tomli-2.4.1-cp313-cp313-macosx_10_13_x86_64.whl", hash = "sha256:36d2bd2ad5fb9eaddba5226aa02c8ec3fa4f192631e347b3ed28186d43be6b54", size = 155866, upload-time = "2026-03-25T20:21:31.65Z" },
-    { url = "https://files.pythonhosted.org/packages/14/6f/12645cf7f08e1a20c7eb8c297c6f11d31c1b50f316a7e7e1e1de6e2e7b7e/tomli-2.4.1-cp313-cp313-macosx_11_0_arm64.whl", hash = "sha256:eb0dc4e38e6a1fd579e5d50369aa2e10acfc9cace504579b2faabb478e76941a", size = 149887, upload-time = "2026-03-25T20:21:33.028Z" },
-    { url = "https://files.pythonhosted.org/packages/5c/e0/90637574e5e7212c09099c67ad349b04ec4d6020324539297b634a0192b0/tomli-2.4.1-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:c7f2c7f2b9ca6bdeef8f0fa897f8e05085923eb091721675170254cbc5b02897", size = 243704, upload-time = "2026-03-25T20:21:34.51Z" },
-    { url = "https://files.pythonhosted.org/packages/10/8f/d3ddb16c5a4befdf31a23307f72828686ab2096f068eaf56631e136c1fdd/tomli-2.4.1-cp313-cp313-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:f3c6818a1a86dd6dca7ddcaaf76947d5ba31aecc28cb1b67009a5877c9a64f3f", size = 251628, upload-time = "2026-03-25T20:21:36.012Z" },
-    { url = "https://files.pythonhosted.org/packages/e3/f1/dbeeb9116715abee2485bf0a12d07a8f31af94d71608c171c45f64c0469d/tomli-2.4.1-cp313-cp313-musllinux_1_2_aarch64.whl", hash = "sha256:d312ef37c91508b0ab2cee7da26ec0b3ed2f03ce12bd87a588d771ae15dcf82d", size = 247180, upload-time = "2026-03-25T20:21:37.136Z" },
-    { url = "https://files.pythonhosted.org/packages/d3/74/16336ffd19ed4da28a70959f92f506233bd7cfc2332b20bdb01591e8b1d1/tomli-2.4.1-cp313-cp313-musllinux_1_2_x86_64.whl", hash = "sha256:51529d40e3ca50046d7606fa99ce3956a617f9b36380da3b7f0dd3dd28e68cb5", size = 251674, upload-time = "2026-03-25T20:21:38.298Z" },
-    { url = "https://files.pythonhosted.org/packages/16/f9/229fa3434c590ddf6c0aa9af64d3af4b752540686cace29e6281e3458469/tomli-2.4.1-cp313-cp313-win32.whl", hash = "sha256:2190f2e9dd7508d2a90ded5ed369255980a1bcdd58e52f7fe24b8162bf9fedbd", size = 97976, upload-time = "2026-03-25T20:21:39.316Z" },
-    { url = "https://files.pythonhosted.org/packages/6a/1e/71dfd96bcc1c775420cb8befe7a9d35f2e5b1309798f009dca17b7708c1e/tomli-2.4.1-cp313-cp313-win_amd64.whl", hash = "sha256:8d65a2fbf9d2f8352685bc1364177ee3923d6baf5e7f43ea4959d7d8bc326a36", size = 108755, upload-time = "2026-03-25T20:21:40.248Z" },
-    { url = "https://files.pythonhosted.org/packages/83/7a/d34f422a021d62420b78f5c538e5b102f62bea616d1d75a13f0a88acb04a/tomli-2.4.1-cp313-cp313-win_arm64.whl", hash = "sha256:4b605484e43cdc43f0954ddae319fb75f04cc10dd80d830540060ee7cd0243cd", size = 95265, upload-time = "2026-03-25T20:21:41.219Z" },
-    { url = "https://files.pythonhosted.org/packages/3c/fb/9a5c8d27dbab540869f7c1f8eb0abb3244189ce780ba9cd73f3770662072/tomli-2.4.1-cp314-cp314-macosx_10_15_x86_64.whl", hash = "sha256:fd0409a3653af6c147209d267a0e4243f0ae46b011aa978b1080359fddc9b6cf", size = 155726, upload-time = "2026-03-25T20:21:42.23Z" },
-    { url = "https://files.pythonhosted.org/packages/62/05/d2f816630cc771ad836af54f5001f47a6f611d2d39535364f148b6a92d6b/tomli-2.4.1-cp314-cp314-macosx_11_0_arm64.whl", hash = "sha256:a120733b01c45e9a0c34aeef92bf0cf1d56cfe81ed9d47d562f9ed591a9828ac", size = 149859, upload-time = "2026-03-25T20:21:43.386Z" },
-    { url = "https://files.pythonhosted.org/packages/ce/48/66341bdb858ad9bd0ceab5a86f90eddab127cf8b046418009f2125630ecb/tomli-2.4.1-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:559db847dc486944896521f68d8190be1c9e719fced785720d2216fe7022b662", size = 244713, upload-time = "2026-03-25T20:21:44.474Z" },
-    { url = "https://files.pythonhosted.org/packages/df/6d/c5fad00d82b3c7a3ab6189bd4b10e60466f22cfe8a08a9394185c8a8111c/tomli-2.4.1-cp314-cp314-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:01f520d4f53ef97964a240a035ec2a869fe1a37dde002b57ebc4417a27ccd853", size = 252084, upload-time = "2026-03-25T20:21:45.62Z" },
-    { url = "https://files.pythonhosted.org/packages/00/71/3a69e86f3eafe8c7a59d008d245888051005bd657760e96d5fbfb0b740c2/tomli-2.4.1-cp314-cp314-musllinux_1_2_aarch64.whl", hash = "sha256:7f94b27a62cfad8496c8d2513e1a222dd446f095fca8987fceef261225538a15", size = 247973, upload-time = "2026-03-25T20:21:46.937Z" },
-    { url = "https://files.pythonhosted.org/packages/67/50/361e986652847fec4bd5e4a0208752fbe64689c603c7ae5ea7cb16b1c0ca/tomli-2.4.1-cp314-cp314-musllinux_1_2_x86_64.whl", hash = "sha256:ede3e6487c5ef5d28634ba3f31f989030ad6af71edfb0055cbbd14189ff240ba", size = 256223, upload-time = "2026-03-25T20:21:48.467Z" },
-    { url = "https://files.pythonhosted.org/packages/8c/9a/b4173689a9203472e5467217e0154b00e260621caa227b6fa01feab16998/tomli-2.4.1-cp314-cp314-win32.whl", hash = "sha256:3d48a93ee1c9b79c04bb38772ee1b64dcf18ff43085896ea460ca8dec96f35f6", size = 98973, upload-time = "2026-03-25T20:21:49.526Z" },
-    { url = "https://files.pythonhosted.org/packages/14/58/640ac93bf230cd27d002462c9af0d837779f8773bc03dee06b5835208214/tomli-2.4.1-cp314-cp314-win_amd64.whl", hash = "sha256:88dceee75c2c63af144e456745e10101eb67361050196b0b6af5d717254dddf7", size = 109082, upload-time = "2026-03-25T20:21:50.506Z" },
-    { url = "https://files.pythonhosted.org/packages/d5/2f/702d5e05b227401c1068f0d386d79a589bb12bf64c3d2c72ce0631e3bc49/tomli-2.4.1-cp314-cp314-win_arm64.whl", hash = "sha256:b8c198f8c1805dc42708689ed6864951fd2494f924149d3e4bce7710f8eb5232", size = 96490, upload-time = "2026-03-25T20:21:51.474Z" },
-    { url = "https://files.pythonhosted.org/packages/45/4b/b877b05c8ba62927d9865dd980e34a755de541eb65fffba52b4cc495d4d2/tomli-2.4.1-cp314-cp314t-macosx_10_15_x86_64.whl", hash = "sha256:d4d8fe59808a54658fcc0160ecfb1b30f9089906c50b23bcb4c69eddc19ec2b4", size = 164263, upload-time = "2026-03-25T20:21:52.543Z" },
-    { url = "https://files.pythonhosted.org/packages/24/79/6ab420d37a270b89f7195dec5448f79400d9e9c1826df982f3f8e97b24fd/tomli-2.4.1-cp314-cp314t-macosx_11_0_arm64.whl", hash = "sha256:7008df2e7655c495dd12d2a4ad038ff878d4ca4b81fccaf82b714e07eae4402c", size = 160736, upload-time = "2026-03-25T20:21:53.674Z" },
-    { url = "https://files.pythonhosted.org/packages/02/e0/3630057d8eb170310785723ed5adcdfb7d50cb7e6455f85ba8a3deed642b/tomli-2.4.1-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:1d8591993e228b0c930c4bb0db464bdad97b3289fb981255d6c9a41aedc84b2d", size = 270717, upload-time = "2026-03-25T20:21:55.129Z" },
-    { url = "https://files.pythonhosted.org/packages/7a/b4/1613716072e544d1a7891f548d8f9ec6ce2faf42ca65acae01d76ea06bb0/tomli-2.4.1-cp314-cp314t-manylinux2014_x86_64.manylinux_2_17_x86_64.manylinux_2_28_x86_64.whl", hash = "sha256:734e20b57ba95624ecf1841e72b53f6e186355e216e5412de414e3c51e5e3c41", size = 278461, upload-time = "2026-03-25T20:21:56.228Z" },
-    { url = "https://files.pythonhosted.org/packages/05/38/30f541baf6a3f6df77b3df16b01ba319221389e2da59427e221ef417ac0c/tomli-2.4.1-cp314-cp314t-musllinux_1_2_aarch64.whl", hash = "sha256:8a650c2dbafa08d42e51ba0b62740dae4ecb9338eefa093aa5c78ceb546fcd5c", size = 274855, upload-time = "2026-03-25T20:21:57.653Z" },
-    { url = "https://files.pythonhosted.org/packages/77/a3/ec9dd4fd2c38e98de34223b995a3b34813e6bdadf86c75314c928350ed14/tomli-2.4.1-cp314-cp314t-musllinux_1_2_x86_64.whl", hash = "sha256:504aa796fe0569bb43171066009ead363de03675276d2d121ac1a4572397870f", size = 283144, upload-time = "2026-03-25T20:21:59.089Z" },
-    { url = "https://files.pythonhosted.org/packages/ef/be/605a6261cac79fba2ec0c9827e986e00323a1945700969b8ee0b30d85453/tomli-2.4.1-cp314-cp314t-win32.whl", hash = "sha256:b1d22e6e9387bf4739fbe23bfa80e93f6b0373a7f1b96c6227c32bef95a4d7a8", size = 108683, upload-time = "2026-03-25T20:22:00.214Z" },
-    { url = "https://files.pythonhosted.org/packages/12/64/da524626d3b9cc40c168a13da8335fe1c51be12c0a63685cc6db7308daae/tomli-2.4.1-cp314-cp314t-win_amd64.whl", hash = "sha256:2c1c351919aca02858f740c6d33adea0c5deea37f9ecca1cc1ef9e884a619d26", size = 121196, upload-time = "2026-03-25T20:22:01.169Z" },
-    { url = "https://files.pythonhosted.org/packages/5a/cd/e80b62269fc78fc36c9af5a6b89c835baa8af28ff5ad28c7028d60860320/tomli-2.4.1-cp314-cp314t-win_arm64.whl", hash = "sha256:eab21f45c7f66c13f2a9e0e1535309cee140182a9cdae1e041d02e47291e8396", size = 100393, upload-time = "2026-03-25T20:22:02.137Z" },
-    { url = "https://files.pythonhosted.org/packages/7b/61/cceae43728b7de99d9b847560c262873a1f6c98202171fd5ed62640b494b/tomli-2.4.1-py3-none-any.whl", hash = "sha256:0d85819802132122da43cb86656f8d1f8c6587d54ae7dcaf30e90533028b49fe", size = 14583, upload-time = "2026-03-25T20:22:03.012Z" },
-]
-
 [[package]]
 name = "tomli-w"
 version = "1.2.0"
@@ -1496,9 +1289,7 @@ dependencies = [
     { name = "pluggy" },
     { name = "pyproject-api" },
     { name = "python-discovery" },
-    { name = "tomli", marker = "python_full_version < '3.11'" },
     { name = "tomli-w" },
-    { name = "typing-extensions", marker = "python_full_version < '3.11'" },
     { name = "virtualenv" },
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/6e/8e/4d2b1b2a81f4de1cd4e54fa40df1ab5f9bb88fe2e37461fc44aba8f9d302/tox-4.58.0.tar.gz", hash = "sha256:ab0b126a04dd56bc18e6d216386db09335247f2289b54cf534deb5c4ae3a8d2e", size = 296926, upload-time = "2026-07-21T13:10:36.622Z" }
@@ -1524,7 +1315,6 @@ version = "1.36.0"
 source = { registry = "https://pypi.org/simple" }
 dependencies = [
     { name = "packaging" },
-    { name = "tomli", marker = "python_full_version < '3.11'" },
     { name = "tox" },
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/56/df/9f90a59de8c87cece6e691eee53dc1cb0a824d73aea8f380ae2f6ecb71de/tox_uv_bare-1.36.0.tar.gz", hash = "sha256:d9b0a2fd0f74fa65d9597108f8a0ef7abb08651c9196a998a6073b781b45cfd0", size = 32548, upload-time = "2026-07-21T13:09:56.435Z" }
@@ -1601,7 +1391,6 @@ source = { registry = "https://pypi.org/simple" }
 dependencies = [
     { name = "click" },
     { name = "h11" },
-    { name = "typing-extensions", marker = "python_full_version < '3.11'" },
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/05/c8/2d307868453a4bca6e64fa3581d122ae0748a0869c53f159339def179c7c/uvicorn-0.52.0.tar.gz", hash = "sha256:ca8876ad6c1983f394157c168b39d52f6dd56dabf5602fa0982751cffc2293ae", size = 97504, upload-time = "2026-07-29T08:45:34.065Z" }
 wheels = [
@@ -1617,7 +1406,6 @@ dependencies = [
     { name = "filelock" },
     { name = "platformdirs" },
     { name = "python-discovery" },
-    { name = "typing-extensions", marker = "python_full_version < '3.11'" },
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/ea/fa/18004e5cb15541ad2a68ff219c755233b012b12d4ec8663d06a258082bec/virtualenv-21.7.1.tar.gz", hash = "sha256:d0dbfaa5483487baea28d7210ef8d24c9d1bd0f10f449eeb215568825a9b334e", size = 5525237, upload-time = "2026-07-30T15:40:36.36Z" }
 wheels = [
@@ -1633,19 +1421,6 @@ dependencies = [
 ]
 sdist = { url = "https://files.pythonhosted.org/packages/cd/41/5e1a4bb12aac5f1493fa1bdc11154eca3b258ca4eba65d39c473fe19d8e9/watchfiles-1.2.0.tar.gz", hash = "sha256:c995fba777f1ea992f090f9236e9284cf7a5d1a0130dd5a3d82c598cacd76838", size = 108252, upload-time = "2026-05-18T04:32:04.251Z" }
 wheels = [
-    { url = "https://files.pythonhosted.org/packages/0d/5a/2bf22ecb24916983bf1cc0095e7dea2741d14d6553b0d6a2ac8bc96eca93/watchfiles-1.2.0-cp310-cp310-macosx_10_12_x86_64.whl", hash = "sha256:bb68bf4df85abebe5efddc53cf2075520f243a59868d9b3973278b23e76962a9", size = 400471, upload-time = "2026-05-18T04:31:08.908Z" },
-    { url = "https://files.pythonhosted.org/packages/55/70/dea1f6a0e76607841a60fb51af150e70124864673f61704abb62b90cdcc7/watchfiles-1.2.0-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:c16cb06dd17d43b9d185094268459eac92c9538356f050e55b54e82cf700e1d4", size = 394599, upload-time = "2026-05-18T04:30:19.845Z" },
-    { url = "https://files.pythonhosted.org/packages/18/52/752dcc7dc817baef5e89518732925795ce52e36a683a9a3c9fb68b21504e/watchfiles-1.2.0-cp310-cp310-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:77a0feab9af4c021c581f695258c642b3d10c5fd4c676e33a0d8606425d82631", size = 455458, upload-time = "2026-05-18T04:30:29.126Z" },
-    { url = "https://files.pythonhosted.org/packages/12/48/366ebbb22fcc504c2f72b45f0b7e72f40a18795cc01752c16066d597b67a/watchfiles-1.2.0-cp310-cp310-manylinux_2_17_armv7l.manylinux2014_armv7l.whl", hash = "sha256:a16ffe19bf5cf9f5edaa1ad1dd830c5a816e8feec430c522302ab55483a4b994", size = 460513, upload-time = "2026-05-18T04:31:40.85Z" },
-    { url = "https://files.pythonhosted.org/packages/ad/44/1f9e1b15e7a729062e0d0c3d0d7225ea4ab98b2267ef87287153be2495fc/watchfiles-1.2.0-cp310-cp310-manylinux_2_17_i686.manylinux2014_i686.whl", hash = "sha256:204f299afcbd65918ab78dbc52626b0ae45e9d8cef403fdbf33ecf9e40eac66e", size = 493616, upload-time = "2026-05-18T04:30:58.47Z" },
-    { url = "https://files.pythonhosted.org/packages/7e/55/8b1086dcc8a1d6a697a62767bd7ea368e74c61c6fd171683cfe24a3fe5d2/watchfiles-1.2.0-cp310-cp310-manylinux_2_17_ppc64le.manylinux2014_ppc64le.whl", hash = "sha256:11743adfa510bfffebe97659fb280182b5c9b238708f667e866f308c3430dc19", size = 573154, upload-time = "2026-05-18T04:30:37.903Z" },
-    { url = "https://files.pythonhosted.org/packages/14/7a/242f400cc77fafa7b18d53d19d9cb64fc6a6f61f28c55913bae7c674d92a/watchfiles-1.2.0-cp310-cp310-manylinux_2_17_s390x.manylinux2014_s390x.whl", hash = "sha256:eb72919d93e3a16fc451d3aa3d4b1698423daca1b382d3d959c9ac51297c12a8", size = 467046, upload-time = "2026-05-18T04:30:41.869Z" },
-    { url = "https://files.pythonhosted.org/packages/02/c8/79eee650c62d2c186598489814468e389b5def0ebe755399ff645b35b1b2/watchfiles-1.2.0-cp310-cp310-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:b62f042afde2dde21ec1d2c1a74361e804673df86f51e418a999c9acfe671b07", size = 457100, upload-time = "2026-05-18T04:31:13.064Z" },
-    { url = "https://files.pythonhosted.org/packages/81/36/519f6dbb7a95e4fe7c1513ed25b1520295ef9905a27f1f2226a73892bfb7/watchfiles-1.2.0-cp310-cp310-manylinux_2_31_riscv64.whl", hash = "sha256:027ae72bfdfd254862065d8b3e2a815c6ab9b1853ce41e6648ece84afd34a551", size = 467038, upload-time = "2026-05-18T04:30:32.915Z" },
-    { url = "https://files.pythonhosted.org/packages/2f/12/951af6b9f89097e02511122258402cb3578443021930b70cf968d6310dc0/watchfiles-1.2.0-cp310-cp310-musllinux_1_1_aarch64.whl", hash = "sha256:e1cfd51e97e13ff3bd047c140764d277fc9b95b7cb5da59e46a47d167adab310", size = 632563, upload-time = "2026-05-18T04:30:11.539Z" },
-    { url = "https://files.pythonhosted.org/packages/28/cc/0cba1f0a6117b7ec117271bdc3cb3a5a252005959755a2c09a745e0942cc/watchfiles-1.2.0-cp310-cp310-musllinux_1_1_x86_64.whl", hash = "sha256:24b2405c0a46738dd9e1cf7135aa5dbdb9d42d024628651b3b13d5117e99f8df", size = 660851, upload-time = "2026-05-18T04:31:53.186Z" },
-    { url = "https://files.pythonhosted.org/packages/d0/f2/26347558cc8bf6877845e66b315f644d03c173906aa09e233a3f4fd23928/watchfiles-1.2.0-cp310-cp310-win32.whl", hash = "sha256:8c520725602756229f045b032a1ff33d7ef0f7404189d62f6c2438cb6d8ef6a1", size = 277023, upload-time = "2026-05-18T04:30:18.825Z" },
-    { url = "https://files.pythonhosted.org/packages/6d/68/a5e67b6b68e94f4c1511d61c46c55eba0737583620b6febf194c7b9cc23f/watchfiles-1.2.0-cp310-cp310-win_amd64.whl", hash = "sha256:03b14855c6f35539e2d95c442ae9530a75762f1e26567152b9ed05f96534a74d", size = 290107, upload-time = "2026-05-18T04:32:09.677Z" },
     { url = "https://files.pythonhosted.org/packages/fc/3d/8024c801df84d1587740d0359e7fdd80afeae3d159011f3d5376dd82f18e/watchfiles-1.2.0-cp311-cp311-macosx_10_12_x86_64.whl", hash = "sha256:704fd259e332e01f9b9c178f4bce9e49027e5587cc2600eeeaf8e76e1c846201", size = 400242, upload-time = "2026-05-18T04:31:19.014Z" },
     { url = "https://files.pythonhosted.org/packages/87/5b/f4dfd45323e949984a3a7f9dc31d1cbb049921e7d98253488dda72ccdaa9/watchfiles-1.2.0-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:6543cf55d170003296d185c0af981f3e1311564907e1f4e08671fc7693a890a5", size = 394562, upload-time = "2026-05-18T04:30:08.46Z" },
     { url = "https://files.pythonhosted.org/packages/98/d8/19483ef075d601c409bce8bcbb5c0f81a10876fff870400568f08ce484a1/watchfiles-1.2.0-cp311-cp311-manylinux_2_17_aarch64.manylinux2014_aarch64.whl", hash = "sha256:89d8c2394a065ca86f5d2910ff263ae67c127e1376ccc4f9fc35c71db879f80a", size = 456611, upload-time = "2026-05-18T04:30:45.723Z" },
@@ -1741,134 +1516,10 @@ wheels = [
     { url = "https://files.pythonhosted.org/packages/e9/f9/45d021e4a5cc7b9dd567f7cbb06d3b75f751a690063fb6cc7ec60f4e46b7/watchfiles-1.2.0-pp311-pypy311_pp73-manylinux_2_17_x86_64.manylinux2014_x86_64.whl", hash = "sha256:a88fc94e647bc4eec523f1caa540258eb71d14278b9daf72fa1e2658a98df0f0", size = 457771, upload-time = "2026-05-18T04:30:56.331Z" },
 ]
 
-[[package]]
-name = "websockets"
-version = "16.1.1"
-source = { registry = "https://pypi.org/simple" }
-resolution-markers = [
-    "python_full_version < '3.11'",
-]
-sdist = { url = "https://files.pythonhosted.org/packages/21/f7/bc3a25c5ec26ce62ce487690becc2f3710bbc7b33338f005ad390db0b986/websockets-16.1.1.tar.gz", hash = "sha256:db234eda965dcce15df96bb9709f587cd87d4d52aaf0e80e2f34ec04c7670c57", size = 182204, upload-time = "2026-07-17T22:51:05.858Z" }
-wheels = [
-    { url = "https://files.pythonhosted.org/packages/08/e7/d1671fb984f9dd844e1da5288070c7c23c9eaba3082d3871aae19c3ab8b9/websockets-16.1.1-cp310-cp310-macosx_10_9_universal2.whl", hash = "sha256:49ae99bdfcae803a885c926bf14f886196e84925395bb3f568fef5c0f0979d7d", size = 179570, upload-time = "2026-07-17T22:48:24.032Z" },
-    { url = "https://files.pythonhosted.org/packages/99/f5/70df723bf571f5e0b1b845e0a4ff1c966eeb84f667599fc251caa37d15a3/websockets-16.1.1-cp310-cp310-macosx_10_9_x86_64.whl", hash = "sha256:5bfd1ac19b1b9986a9c95a82d5e23a391ebb09e12c34d7be6094b86efcc35731", size = 177252, upload-time = "2026-07-17T22:48:25.775Z" },
-    { url = "https://files.pythonhosted.org/packages/90/72/2f14b2e167170b8bf1c8bb7f9b0d78000f470d41a2085a91f33e3917b6c9/websockets-16.1.1-cp310-cp310-macosx_11_0_arm64.whl", hash = "sha256:9246a0d063cfcbcc85f2359dd6876d681213f4790832272aa16641b4ed5d64d4", size = 177530, upload-time = "2026-07-17T22:48:27.337Z" },
-    { url = "https://files.pythonhosted.org/packages/f3/18/a17e2f0cde02dc10154c808deed7e1d8528afff93612f70d3f0a5b19b011/websockets-16.1.1-cp310-cp310-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl", hash = "sha256:1214e673c404684b9bf7154f5cf43b45025b1a6160fac3a9e438e9c1a97e22cb", size = 186038, upload-time = "2026-07-17T22:48:28.756Z" },
-    { url = "https://files.pythonhosted.org/packages/d5/b0/41de283899cf5929d637b72a508cdbc9aa40dc0f317c6b77613fd1000488/websockets-16.1.1-cp310-cp310-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:90001d893bc368e302ef168d82130b4e4fdd27b85fa094682df9b667c2d48838", size = 187278, upload-time = "2026-07-17T22:48:30.328Z" },
-    { url = "https://files.pythonhosted.org/packages/50/61/874aab5257e027f9f61b5004cec65e592babca7942b1bc09f38e72b7f1fd/websockets-16.1.1-cp310-cp310-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl", hash = "sha256:130937b167a52af203c8d58e78d67705874e82759862e3b9671a452fec4abc87", size = 189936, upload-time = "2026-07-17T22:48:31.896Z" },
-    { url = "https://files.pythonhosted.org/packages/a6/1a/42173913ac5519607220849ed417c864d77384e4119f06dbba964a50f096/websockets-16.1.1-cp310-cp310-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl", hash = "sha256:9c9f23004a3d40e89c01a7955d186a6cc83418d93b749701944ce2de3e95a1f3", size = 187796, upload-time = "2026-07-17T22:48:33.344Z" },
-    { url = "https://files.pythonhosted.org/packages/1b/f4/37c1840bd89b529479aec41470b97b7c683b107ca90b6399ac5afb99dedf/websockets-16.1.1-cp310-cp310-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl", hash = "sha256:f55f0b01956a094c8587146d9558c91937e78789c333860ffaf35931a6e5dbc4", size = 186481, upload-time = "2026-07-17T22:48:34.843Z" },
-    { url = "https://files.pythonhosted.org/packages/9e/70/652d9b964adcfbeb056f42e0ca6bece34d108fe75534e74df20643cae199/websockets-16.1.1-cp310-cp310-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl", hash = "sha256:6aaface73b9c71974c6497366d8b9628357f6c9749e09c4ea3610176c63f2ae3", size = 184351, upload-time = "2026-07-17T22:48:36.307Z" },
-    { url = "https://files.pythonhosted.org/packages/13/f1/af3850e5d48d482921985be72ebcb169c6180b3a77b57bd612deebcee23b/websockets-16.1.1-cp310-cp310-musllinux_1_2_aarch64.whl", hash = "sha256:dc0fad4933f427acd5b1cec210f3ea6dce7089e1724e4b9ec6ef47c6c04d1b3b", size = 186791, upload-time = "2026-07-17T22:48:37.762Z" },
-    { url = "https://files.pythonhosted.org/packages/1d/40/1a4e3ed4969ec378dcad337e5f1472c5e292cb3e733bc392f0dc2e230abd/websockets-16.1.1-cp310-cp310-musllinux_1_2_armv7l.whl", hash = "sha256:f2769a0344a09e9ccf5b3cce538bc75a51b53eff3275d3896310c8552049195d", size = 185413, upload-time = "2026-07-17T22:48:39.127Z" },
-    { url = "https://files.pythonhosted.org/packages/aa/3e/4e3fa1afe8f1a6a780434cd9ba8eb422632b044eff3dd73f6af67523c147/websockets-16.1.1-cp310-cp310-musllinux_1_2_ppc64le.whl", hash = "sha256:f70541f3104339f59f830522d94ebadb1bf47426287381623443d8bb1cdbf33d", size = 187178, upload-time = "2026-07-17T22:48:40.676Z" },
-    { url = "https://files.pythonhosted.org/packages/71/ab/dd742766aa5dda7f349be0de49e4d565b84cf6f7f7fa02e07692f0f2bdd9/websockets-16.1.1-cp310-cp310-musllinux_1_2_riscv64.whl", hash = "sha256:dc385593a42e31cd6fb60c19f0ecb015b386603818fc2c6c274fb42bd2bb4165", size = 185051, upload-time = "2026-07-17T22:48:42.098Z" },
-    { url = "https://files.pythonhosted.org/packages/ae/f5/76438c6560f416f1c0a7f587679fb97cc6e99ed336011d43ce2002dd27c1/websockets-16.1.1-cp310-cp310-musllinux_1_2_s390x.whl", hash = "sha256:387e8e4aa5df2f90b198fa3cad3478822a89cf905b6a6d6c97dc3664689640cc", size = 185846, upload-time = "2026-07-17T22:48:43.472Z" },
-    { url = "https://files.pythonhosted.org/packages/62/12/5c0320f2127823d27b2d56d611d31b0b284ad4edcb41364d66bf4c92b537/websockets-16.1.1-cp310-cp310-musllinux_1_2_x86_64.whl", hash = "sha256:fd46fff7eb62c24804d234f0051c7a8ea81285ad63e0337d3dcf33ca82aee58a", size = 186066, upload-time = "2026-07-17T22:48:44.884Z" },
-    { url = "https://files.pythonhosted.org/packages/a2/97/875986b857b955c3f9dd192cb8a1af81254dfb2ea22cc9590f0a1e020b8b/websockets-16.1.1-cp310-cp310-win32.whl", hash = "sha256:7883388947767080f094950b342b30d35a2a06b849cd967c422fa0db72b40ea9", size = 179940, upload-time = "2026-07-17T22:48:46.481Z" },
-    { url = "https://files.pythonhosted.org/packages/54/82/1013a5fe7ddae8e102bc3b4b39db81d8d28fd02100a324ce6ede8cd832b1/websockets-16.1.1-cp310-cp310-win_amd64.whl", hash = "sha256:d57685547e0060cc6fd90ee6a28405d6bd395e525545f13c8d7cd99c78afd79f", size = 180239, upload-time = "2026-07-17T22:48:48.043Z" },
-    { url = "https://files.pythonhosted.org/packages/2b/03/47debfe28e9d6d354be5d777b67fd44c359b9eb299a5d103500bd7cc3e37/websockets-16.1.1-cp311-cp311-macosx_10_9_universal2.whl", hash = "sha256:d0fcf657e9f13ff4b177960ab2200237b12994232dfb6df16f1cfe1d4339f93c", size = 179566, upload-time = "2026-07-17T22:48:49.596Z" },
-    { url = "https://files.pythonhosted.org/packages/72/93/31efa1ed78c17e5cfc229fd449e3966e1b9cc15753204cd585cc8dd01f4a/websockets-16.1.1-cp311-cp311-macosx_10_9_x86_64.whl", hash = "sha256:b852788aa51764e2d8e4cf5493d559326bcae5e38d16ba25ffa322b034df272a", size = 177250, upload-time = "2026-07-17T22:48:50.942Z" },
-    { url = "https://files.pythonhosted.org/packages/01/4a/542378ab3972b0c1cf1df3df3eff9591cea0d30c58c3aa3c4ddbc244e787/websockets-16.1.1-cp311-cp311-macosx_11_0_arm64.whl", hash = "sha256:1427fb4cf0d72f66333e2cacc3ff5f575bf2d7008166ce991a4a470b21d51a22", size = 177528, upload-time = "2026-07-17T22:48:52.59Z" },
-    { url = "https://files.pythonhosted.org/packages/33/d9/162321f63c7eed558e9e1798ed7a1e34a4f6dab51f35419e4ed7a4907979/websockets-16.1.1-cp311-cp311-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl", hash = "sha256:da4ca1a9d72f9030b3146b8d7022719a9f3d478f61efe6f7dd51d243f61c51b2", size = 186859, upload-time = "2026-07-17T22:48:53.915Z" },
-    { url = "https://files.pythonhosted.org/packages/de/09/87df740f7430ce564bd52402e9c9458d4d0459cc7d2ee29e530c8204851b/websockets-16.1.1-cp311-cp311-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:86d7f0f8bdb25d2c632b72527325e4776430fd5bc61b9118de4e2b8ddb5f5b01", size = 188095, upload-time = "2026-07-17T22:48:55.384Z" },
-    { url = "https://files.pythonhosted.org/packages/d2/12/3d2703af7cc095f3c81904c92208cc1ae79affbc67376944b50ee9301f73/websockets-16.1.1-cp311-cp311-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl", hash = "sha256:7dfcad78ea1492ee3a9ec765cb7f51bbc17d477107aaf6b22abf7b2558d1c5a0", size = 191385, upload-time = "2026-07-17T22:48:56.742Z" },
-    { url = "https://files.pythonhosted.org/packages/1d/69/986aa0234a964a00f5149cfc46e136e96c8faad1c783474550f40d31aef4/websockets-16.1.1-cp311-cp311-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl", hash = "sha256:fb9a0a6dc3d1b3986cb88091b6899f0396651e0f74e2c9766ab8d6ffc3842e29", size = 188653, upload-time = "2026-07-17T22:48:58.134Z" },
-    { url = "https://files.pythonhosted.org/packages/35/6b/10f9d03e3970a69ba67bd3b46b87a929b586d0300fadbfe14f57c1f85490/websockets-16.1.1-cp311-cp311-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl", hash = "sha256:29dfa8114c4a620c69591c5973860f768eac29d3fd6904f37f34266cb219c512", size = 187426, upload-time = "2026-07-17T22:48:59.515Z" },
-    { url = "https://files.pythonhosted.org/packages/56/db/bb3aad62bf63d8bb3f0634b2eabffcfb3677a34bd19492110ff6869cf703/websockets-16.1.1-cp311-cp311-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl", hash = "sha256:6ff9417c0ada4d0f7d212f928303e5579bdf3ace4c802fa4afabb30995da58c3", size = 184882, upload-time = "2026-07-17T22:49:00.916Z" },
-    { url = "https://files.pythonhosted.org/packages/6c/4c/c09a2ea9bfbeccce52fdc383e5f28af4bc8843338aabac28c81489af6120/websockets-16.1.1-cp311-cp311-musllinux_1_2_aarch64.whl", hash = "sha256:8fe0b50da2d84535fb4f7b4bfa951280f97ce3d558a0443b541166d609e67b57", size = 187584, upload-time = "2026-07-17T22:49:02.283Z" },
-    { url = "https://files.pythonhosted.org/packages/c7/8b/31bb4eb4d9eaacf1fdd39d115772a8aeaedfc19b5dc262e57ffbc8a9d42c/websockets-16.1.1-cp311-cp311-musllinux_1_2_armv7l.whl", hash = "sha256:34420aaa64440ebd51ac72ca8a45ef4626429438c9b02e633ae412ed43f925d3", size = 186174, upload-time = "2026-07-17T22:49:03.973Z" },
-    { url = "https://files.pythonhosted.org/packages/2f/e4/dc02d725610a1ad49e193ef91a548194d71bdc6cdf27da83067dd1f73995/websockets-16.1.1-cp311-cp311-musllinux_1_2_ppc64le.whl", hash = "sha256:a6a61aff018180c9c50b7b0da33bfd29d378af3497429c95006c589a23a11648", size = 187986, upload-time = "2026-07-17T22:49:05.553Z" },
-    { url = "https://files.pythonhosted.org/packages/e0/73/30ed84c8bfd14c73d4af29d5ed9323c3073b48e0b7b23b67070f4e7fd59b/websockets-16.1.1-cp311-cp311-musllinux_1_2_riscv64.whl", hash = "sha256:04fd29a0e2fe9414a95b00e92c67ae51bf900c50c0f8a4b2dafdad621f49ea1d", size = 185565, upload-time = "2026-07-17T22:49:06.959Z" },
-    { url = "https://files.pythonhosted.org/packages/7d/d3/4be8d4959f51e31b4f8fc0ece12b45bd3b6c0d15ea23b9990d9c11fc805f/websockets-16.1.1-cp311-cp311-musllinux_1_2_s390x.whl", hash = "sha256:5c31aa7e39ee3e8a358573257f1c0bb5c52430d1b637030dd9c8cc2c282926be", size = 186598, upload-time = "2026-07-17T22:49:08.293Z" },
-    { url = "https://files.pythonhosted.org/packages/26/fa/abb38597a52d84ed9cfacadc7a0c6f2db282c0ab23cdf72b58a666a21227/websockets-16.1.1-cp311-cp311-musllinux_1_2_x86_64.whl", hash = "sha256:d14bfb217eb4701e850f1525c9d29d79c44794cdf1c299ead25f39f8c78dea81", size = 186834, upload-time = "2026-07-17T22:49:09.766Z" },
-    { url = "https://files.pythonhosted.org/packages/59/80/1119ad08a228b90c4eb77fbe48df7836731a605f5f881ba701ca826a4a65/websockets-16.1.1-cp311-cp311-win32.whl", hash = "sha256:2e28e602bb13da44fbe518c1781a88e3b9d4c3d48d02c9bad83e546164336f57", size = 179940, upload-time = "2026-07-17T22:49:11.196Z" },
-    { url = "https://files.pythonhosted.org/packages/71/b2/e511c1c6f64a95c2f3fc54bffda0e14eaa7e9442be605c29270f7589b918/websockets-16.1.1-cp311-cp311-win_amd64.whl", hash = "sha256:7421fad442de870a8cbf2287d1cad7e706ece0dbfeba5e911df132cbdc1cb56a", size = 180239, upload-time = "2026-07-17T22:49:12.519Z" },
-    { url = "https://files.pythonhosted.org/packages/17/9d/681cda21c9eee743203a6cb79b9d3d05adad9aa60ec660c6c9bf4dd619ca/websockets-16.1.1-cp312-cp312-macosx_10_13_universal2.whl", hash = "sha256:cc97814dfb786a83b6e2dc2e79351e1b83e6d715647d6887fcabd83026417a00", size = 179600, upload-time = "2026-07-17T22:49:13.92Z" },
-    { url = "https://files.pythonhosted.org/packages/fb/8d/6195a88b45e8d2a8f745fc2046e36f885a3c9763e6767d2c46229bf9510c/websockets-16.1.1-cp312-cp312-macosx_10_13_x86_64.whl", hash = "sha256:e047dc87ef7ca50f4d309bf775ad4a71711c58556d75d7bd0604b2317f43e94b", size = 177272, upload-time = "2026-07-17T22:49:15.453Z" },
-    { url = "https://files.pythonhosted.org/packages/73/e3/fe2d498c64dea0095c9a9f9a351af4cd6eef31b618395582bc1f38ba45ff/websockets-16.1.1-cp312-cp312-macosx_11_0_arm64.whl", hash = "sha256:01fbdcbac298efe19360b94bc0039c8f746f0220ba570f327577bfee81059175", size = 177542, upload-time = "2026-07-17T22:49:16.875Z" },
-    { url = "https://files.pythonhosted.org/packages/fe/ed/f1831681fce0e3242346e5458486003c5f124ed69e5e0b847fd029db4973/websockets-16.1.1-cp312-cp312-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl", hash = "sha256:0f62863e8a00a6d33c3d6566ec0b89f23787b747ffe0c3bc71ec0e76b82c94b1", size = 187137, upload-time = "2026-07-17T22:49:18.323Z" },
-    { url = "https://files.pythonhosted.org/packages/6f/79/4ff9dcc1bb46f6b4c536936dde1fd60f9b564f3304307274db97f4c9496d/websockets-16.1.1-cp312-cp312-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:8087e82f842609734c9b5a1330464f8e94e346ba0e18c832c08bafa4b0d63c15", size = 188374, upload-time = "2026-07-17T22:49:19.65Z" },
-    { url = "https://files.pythonhosted.org/packages/62/c3/5c49b6efb36cab733d23773f6de575e1dba65736ead17d5d2b2a1daef779/websockets-16.1.1-cp312-cp312-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl", hash = "sha256:2bb5d041a8307d2e18782e7ce777f6fdb1e8c2f5d09291484b18c294b789d9aa", size = 191155, upload-time = "2026-07-17T22:49:21.331Z" },
-    { url = "https://files.pythonhosted.org/packages/6e/f6/56ccceda3a4838d18f1d40821480da4775397e8b1eecf4031e20c50e2e90/websockets-16.1.1-cp312-cp312-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl", hash = "sha256:1db4de4a0e95673f7545d393c49eeb0c2f18ac1ef93073218c79d5cdb2ee75ab", size = 189011, upload-time = "2026-07-17T22:49:22.889Z" },
-    { url = "https://files.pythonhosted.org/packages/86/d6/ad5286241a2bce1107e2798d3bfbd62cf79aee167bdb654f8cb1e9dbf949/websockets-16.1.1-cp312-cp312-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl", hash = "sha256:f17dbe07eb3ea7f99e4df9b7e0efefe80fbf30d37a8cc4d561a0aed310bc8847", size = 187766, upload-time = "2026-07-17T22:49:24.339Z" },
-    { url = "https://files.pythonhosted.org/packages/bc/67/d65c970b7e347fdca69479beb7811c2060529956730a7a4e3ae7c66b0e31/websockets-16.1.1-cp312-cp312-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl", hash = "sha256:4b57693728576d84ede0a77987ab16881b783d2cd9f1dc180a8fbbc3f79c4428", size = 185173, upload-time = "2026-07-17T22:49:25.743Z" },
-    { url = "https://files.pythonhosted.org/packages/1d/5b/14af3cd4ee69d8ea9baca58f3dc3cfb1ba78332a347fd478cb096549d60e/websockets-16.1.1-cp312-cp312-musllinux_1_2_aarch64.whl", hash = "sha256:2a636ff1e7a5c4edf71ef0e79adae7f25dba93b4fcbe3dc958733477ffeb0eaf", size = 187809, upload-time = "2026-07-17T22:49:27.147Z" },
-    { url = "https://files.pythonhosted.org/packages/7b/11/be301710d70de97e3e7b3586e6d492c9c06d6a61bf1c2202c36cf0c75607/websockets-16.1.1-cp312-cp312-musllinux_1_2_armv7l.whl", hash = "sha256:d6bec75c290fe484a8ba4cacdf838501e17c06ecfbbf31eede81a9e431bd7751", size = 186412, upload-time = "2026-07-17T22:49:28.611Z" },
-    { url = "https://files.pythonhosted.org/packages/db/07/fe1435bf6fe738a3d3b54dbe0c18dabf12cba4d909ac8b58b539ce27c1f4/websockets-16.1.1-cp312-cp312-musllinux_1_2_ppc64le.whl", hash = "sha256:54509b8e92fee4453e152b7558ddef37ce9705a044922f2095a6105e3f80c96f", size = 188290, upload-time = "2026-07-17T22:49:29.965Z" },
-    { url = "https://files.pythonhosted.org/packages/8a/0a/81f394aff8efcbb01208c1ced77df0a3c7fcce584a88c7273663697946c2/websockets-16.1.1-cp312-cp312-musllinux_1_2_riscv64.whl", hash = "sha256:f0aa4aad3b1b69ad3fd85a0fd0952ec64331c762bd77ec51cc814170873890b2", size = 185844, upload-time = "2026-07-17T22:49:31.447Z" },
-    { url = "https://files.pythonhosted.org/packages/39/5c/dd485b995473f415510251fe9bd708f2d24458f439fce958daf8d66dc7c6/websockets-16.1.1-cp312-cp312-musllinux_1_2_s390x.whl", hash = "sha256:42290eb6db4ccaca7012656738214f8514082fb6fa40cdeb61bb9a471b52e383", size = 186823, upload-time = "2026-07-17T22:49:33.104Z" },
-    { url = "https://files.pythonhosted.org/packages/9d/0b/f78de76ff446f1e66af12b43c48a35f31744de93cfdec2f4ea67d5d7bbf1/websockets-16.1.1-cp312-cp312-musllinux_1_2_x86_64.whl", hash = "sha256:53260c8930da5771cec89439bff99c20c8cb03ddb9588b980697355a83cd4bd3", size = 187102, upload-time = "2026-07-17T22:49:34.616Z" },
-    { url = "https://files.pythonhosted.org/packages/37/a1/4cf892007778eaf84ad162bfc98046e0ed89b63ac55949e3236626b2a23f/websockets-16.1.1-cp312-cp312-win32.whl", hash = "sha256:1d27fa8462ad6a1cb36206a3d0640b2333340def181fae11ed7f9adeaa5c0747", size = 179943, upload-time = "2026-07-17T22:49:36.213Z" },
-    { url = "https://files.pythonhosted.org/packages/d9/de/6abe251d28c3a3f217096575400b27750b18e0b1d2fff3a2a239960fea07/websockets-16.1.1-cp312-cp312-win_amd64.whl", hash = "sha256:b436f6ec4fc3a6b4237c84d3f83170ed2b40bb584222f0ac47a0c8a5921980c7", size = 180243, upload-time = "2026-07-17T22:49:37.626Z" },
-    { url = "https://files.pythonhosted.org/packages/ce/fd/6ec6c6d2850aea25b1b2aa9901a016980bb87d01e89b3eb00470b1b5d471/websockets-16.1.1-cp313-cp313-macosx_10_13_universal2.whl", hash = "sha256:ab59169ace05dcb49a1d4118f0bde139557adf45091bd85747e36bf5de984dd1", size = 179587, upload-time = "2026-07-17T22:49:38.959Z" },
-    { url = "https://files.pythonhosted.org/packages/5f/d8/1d299d2dd34087db39831a34cc645ef8a6f89d78efada6983093513cd81c/websockets-16.1.1-cp313-cp313-macosx_10_13_x86_64.whl", hash = "sha256:5e3b7d601f6f84156b08cc4a5e541c2b50ad7b36cfc302b657a12477c904a5df", size = 177272, upload-time = "2026-07-17T22:49:40.293Z" },
-    { url = "https://files.pythonhosted.org/packages/3d/86/0a70d3ae2f0f2256bb41302d9804dbca65d4360281e7feb3e1f94102ac46/websockets-16.1.1-cp313-cp313-macosx_11_0_arm64.whl", hash = "sha256:cd2ca96a082a36964aca83e992f72abeb61b7306c1a6cba4c7d06a7b93750cac", size = 177530, upload-time = "2026-07-17T22:49:41.786Z" },
-    { url = "https://files.pythonhosted.org/packages/b5/c2/c676c69444d9db448b3f0a55a98dcc534affce0bce961d9d2f0b8499b10a/websockets-16.1.1-cp313-cp313-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl", hash = "sha256:f5d497865f05bb222cab7016c6034542e84e5f29f49c6fd3f4939cda7197b5b8", size = 187197, upload-time = "2026-07-17T22:49:43.658Z" },
-    { url = "https://files.pythonhosted.org/packages/0b/13/88137fbaf726ebe29d62c1117fa11fa2bbb6209dc79d4ad738efbe36a2aa/websockets-16.1.1-cp313-cp313-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:bae954c382e013d5ea5b190d2830526bfa45ad121c326da0049b8c769f185db6", size = 188433, upload-time = "2026-07-17T22:49:45.147Z" },
-    { url = "https://files.pythonhosted.org/packages/01/6d/46c2f2ce6751cb26f39293e1ecbf8544cb01321397cd476c2756b98c216d/websockets-16.1.1-cp313-cp313-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl", hash = "sha256:e09f753a169951eb4f28c2c774f71069304f66e7277e0f5a2892423599cfa854", size = 189868, upload-time = "2026-07-17T22:49:46.581Z" },
-    { url = "https://files.pythonhosted.org/packages/29/2b/170a9e8097636cfde4dc3c592b6e00b18a44a2f5407606d96ca542dd5838/websockets-16.1.1-cp313-cp313-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl", hash = "sha256:024193f8551a2b0eafbdd160911012c4e6c228c28430c84433253299a9e42d6a", size = 189059, upload-time = "2026-07-17T22:49:47.972Z" },
-    { url = "https://files.pythonhosted.org/packages/a7/48/f0d4ebc9ab4b473b8861b9e20fdb663d515d42f7befdf62cdb60fee7a1ec/websockets-16.1.1-cp313-cp313-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl", hash = "sha256:aabe464bfd13bd25f4821faf111da6fefdc389f870265a53105580e45b0a2e49", size = 187814, upload-time = "2026-07-17T22:49:49.344Z" },
-    { url = "https://files.pythonhosted.org/packages/d5/ba/39a41d3ae8e72696a9492581900611c5a91e2b07563b0bcd2523adea9854/websockets-16.1.1-cp313-cp313-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl", hash = "sha256:a28fcbc9b6baf54a2e23f8655f308e4ccc6afdd7266f8fe7954f320dcda0f785", size = 185229, upload-time = "2026-07-17T22:49:50.787Z" },
-    { url = "https://files.pythonhosted.org/packages/3c/36/ac15b604f850d1907f0a85ed721cefe47cd45034b3620069b829746cccbe/websockets-16.1.1-cp313-cp313-musllinux_1_2_aarch64.whl", hash = "sha256:79eace538c6a97e96d0d03d4f9d314f9677f5ed85a8a984992ffd90b13cb8a56", size = 187874, upload-time = "2026-07-17T22:49:52.228Z" },
-    { url = "https://files.pythonhosted.org/packages/a8/f3/3fbd5d71d59299c3770faa5884d4f45070236ca5a35ab3a61830812c409a/websockets-16.1.1-cp313-cp313-musllinux_1_2_armv7l.whl", hash = "sha256:496af849a472b531f758dbd4d61338f5000538cb1a7b3d20d9d32a264517f509", size = 186469, upload-time = "2026-07-17T22:49:53.776Z" },
-    { url = "https://files.pythonhosted.org/packages/b4/fc/dd90349bba58af2a53ef2ddd9c32716c81eb6d59a0687939fff561860878/websockets-16.1.1-cp313-cp313-musllinux_1_2_ppc64le.whl", hash = "sha256:5283810d2646741a0d8da2aa733d6aefa0545809afccb2a5d105a26bc45125f1", size = 188347, upload-time = "2026-07-17T22:49:55.202Z" },
-    { url = "https://files.pythonhosted.org/packages/4c/f3/f73ba86427682da59b78c11d77ba56d5b801c32e84afe79b274bbd6a9bb2/websockets-16.1.1-cp313-cp313-musllinux_1_2_riscv64.whl", hash = "sha256:4e3b680b1e0a27457e727a0d572fd81dffa87b6dbf8b228ab57da64f7d85aead", size = 185903, upload-time = "2026-07-17T22:49:56.75Z" },
-    { url = "https://files.pythonhosted.org/packages/34/7c/f95eb20e80104173b3a0a092291f89ea4047ef6e608e0a57ca06eb14eecb/websockets-16.1.1-cp313-cp313-musllinux_1_2_s390x.whl", hash = "sha256:69159730a823dde3ea8d08783e8d47ef135a6d7e8d44eb127e32b321c9db8e3e", size = 186855, upload-time = "2026-07-17T22:49:58.467Z" },
-    { url = "https://files.pythonhosted.org/packages/b0/35/dd875b3e050ff232d60fa377707f890e369f74d134f1be32e8f68879747c/websockets-16.1.1-cp313-cp313-musllinux_1_2_x86_64.whl", hash = "sha256:ed5bb271084b46530ee2ddc0410537a9961152c5ccba2fc98c5276d992ccba87", size = 187140, upload-time = "2026-07-17T22:50:00.016Z" },
-    { url = "https://files.pythonhosted.org/packages/e8/dc/5cbfcb41824502f6af93b8f3943a4d06c67c23c7d2e31eb18748c4a5b2a7/websockets-16.1.1-cp313-cp313-win32.whl", hash = "sha256:cfb70b4eb56cac4da0a83588f3ad50d46beb0690391082f3d4e2d488c70b68ea", size = 179928, upload-time = "2026-07-17T22:50:01.685Z" },
-    { url = "https://files.pythonhosted.org/packages/b0/c1/71e5deb5b7f8f226997ab64908c184ac3105c0155ce2d486f318e5dd08a8/websockets-16.1.1-cp313-cp313-win_amd64.whl", hash = "sha256:d9531d9cbeac99af6f038fb1bc351403531f7d634a2c2e10e2f7c854c6ed5b68", size = 180242, upload-time = "2026-07-17T22:50:03.117Z" },
-    { url = "https://files.pythonhosted.org/packages/73/a2/ba78a164eeea4620df4a4df4bd2ed6017438c4655cc0f36f2c0bc0432355/websockets-16.1.1-cp314-cp314-macosx_10_15_universal2.whl", hash = "sha256:443aefe96b7fdb132e2a70806cca1f2af49bb3f28e47abcd7c2e9dcf4d8fa1b8", size = 179635, upload-time = "2026-07-17T22:50:05.001Z" },
-    { url = "https://files.pythonhosted.org/packages/b9/08/d26d7a7628cd4ac34cbbdb63ac80914ca842ed8e42938c40a53567806df3/websockets-16.1.1-cp314-cp314-macosx_10_15_x86_64.whl", hash = "sha256:6456ff333092d509127d75a638cb411afae8ff17f092635015d1902efec8a293", size = 177320, upload-time = "2026-07-17T22:50:06.427Z" },
-    { url = "https://files.pythonhosted.org/packages/0f/45/ebec83e6269536aa5932533c67b0af5c781f3e73fdbcd68672dcf43f4f44/websockets-16.1.1-cp314-cp314-macosx_11_0_arm64.whl", hash = "sha256:fce6c48559c86d1ac3632ccb1bebc7d5442fbe79bd9bb0e40379ee54be2a4051", size = 177544, upload-time = "2026-07-17T22:50:07.834Z" },
-    { url = "https://files.pythonhosted.org/packages/c9/d5/abc614d2297f6c1c3e01e61260364457a47c25cc1cf6a879038902bc6aa8/websockets-16.1.1-cp314-cp314-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl", hash = "sha256:92b820d345f7a3fc7b8163949ee92df910f290c3fc517b3d5301c78065adafe1", size = 187270, upload-time = "2026-07-17T22:50:09.275Z" },
-    { url = "https://files.pythonhosted.org/packages/52/71/4c99af3b87dff1b2927981f6876607d4acb45338c665242168d3982f7758/websockets-16.1.1-cp314-cp314-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:2a606d9c24035242a3e256e9d5b77ed9cd6bccfcb7cf993e5ca3c0f6f68fb6a7", size = 188509, upload-time = "2026-07-17T22:50:10.722Z" },
-    { url = "https://files.pythonhosted.org/packages/9b/b4/5c8ca14b0df7eb84ed0524165c5359150210140817a3312aee57bf62a1cf/websockets-16.1.1-cp314-cp314-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl", hash = "sha256:414e596c75f74e0994084694189d7dc9229fb278e33064d6784b73ffbba3ca31", size = 189882, upload-time = "2026-07-17T22:50:12.293Z" },
-    { url = "https://files.pythonhosted.org/packages/25/c1/bedfba9e70557129cb8083748d167bdcc01483dedf0f0df143676df05cbe/websockets-16.1.1-cp314-cp314-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl", hash = "sha256:536676848fc5961aca9d20389951f59169508f765637a172403dc5434d722fa0", size = 189114, upload-time = "2026-07-17T22:50:13.789Z" },
-    { url = "https://files.pythonhosted.org/packages/df/09/aa835b2787835aebd839114be5de51b797cb480b63ba42b26d34dfe147cb/websockets-16.1.1-cp314-cp314-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl", hash = "sha256:97fd3a0e8b53efa41970ac1dff3d8cf0d2884cadeb4caaf95db7ad1526926ee3", size = 187861, upload-time = "2026-07-17T22:50:15.179Z" },
-    { url = "https://files.pythonhosted.org/packages/20/26/f6408330694dbc9830857d9d23bc14ac4f6875127a480cfdda8d5ca21198/websockets-16.1.1-cp314-cp314-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl", hash = "sha256:7b1b19636af86a3c7995d4d028dbe376f39b4bf31541146f9c123582a6c94562", size = 185286, upload-time = "2026-07-17T22:50:16.741Z" },
-    { url = "https://files.pythonhosted.org/packages/17/9a/e0675e70dd8a80762cf35bb18799d3f290a4890ffe6439bc51d222796083/websockets-16.1.1-cp314-cp314-musllinux_1_2_aarch64.whl", hash = "sha256:41c8e77f17294c0ac18008a7309b99b34ee72247ef10b6dff4c3f8b5ac29896b", size = 187935, upload-time = "2026-07-17T22:50:18.213Z" },
-    { url = "https://files.pythonhosted.org/packages/33/c1/3234cfb86afde01b81e9bddcc6e534c440975d60a13991259e833069ab3e/websockets-16.1.1-cp314-cp314-musllinux_1_2_armv7l.whl", hash = "sha256:9f63bcef7f4b02b06b35fc01c93b96c43b5e88e1e8868676caacf493d5a31f3a", size = 186444, upload-time = "2026-07-17T22:50:19.67Z" },
-    { url = "https://files.pythonhosted.org/packages/89/87/9c15206e1d778923d8daa9657de07aa62ea815e13448319c98458c37b281/websockets-16.1.1-cp314-cp314-musllinux_1_2_ppc64le.whl", hash = "sha256:dab9eb87869da2d6ed3af3f3adf28414baae6ec9d4df355ffc18889132f3436c", size = 188409, upload-time = "2026-07-17T22:50:21.28Z" },
-    { url = "https://files.pythonhosted.org/packages/f2/00/cf5de5c67676de2d3eef8b2a518f168f6796595447a5b7161ba0d012915c/websockets-16.1.1-cp314-cp314-musllinux_1_2_riscv64.whl", hash = "sha256:43e3a9fdd7cbf7ba6040c31fae0faf84ca1474fef777c4e37912f1540f854499", size = 185958, upload-time = "2026-07-17T22:50:22.719Z" },
-    { url = "https://files.pythonhosted.org/packages/62/c0/731b6ddede2e4136912ec4cff2cffbda35af73546be4762c3d7bd3bd79af/websockets-16.1.1-cp314-cp314-musllinux_1_2_s390x.whl", hash = "sha256:056ae37939ed7e9974f364f5864e76e49182622d8f9751ac1903c0d09b013985", size = 186911, upload-time = "2026-07-17T22:50:24.108Z" },
-    { url = "https://files.pythonhosted.org/packages/8c/7f/39c634472c4469a24a7c09cecddffb08fac6d0e74f73881a94ee8a40a196/websockets-16.1.1-cp314-cp314-musllinux_1_2_x86_64.whl", hash = "sha256:a0eadbbf2c30f01efa58e1f110eb6fa293261f6b0b1aa38f7f48707107690af9", size = 187204, upload-time = "2026-07-17T22:50:25.548Z" },
-    { url = "https://files.pythonhosted.org/packages/26/89/9667c256c256dafcc62d21328ce7a40067da857969b68ee9af375b0aaf72/websockets-16.1.1-cp314-cp314-win32.whl", hash = "sha256:195c978b065fa40910582464f99d6b15c8b314c68e0546549a55ed83f4735328", size = 179603, upload-time = "2026-07-17T22:50:27.086Z" },
-    { url = "https://files.pythonhosted.org/packages/bd/dd/1c099d6c0fc5deb6b46ccdbb6981fdb4b12c917869cb3952408409dc18db/websockets-16.1.1-cp314-cp314-win_amd64.whl", hash = "sha256:4e8d01cc3bcae7bbf8167f944aeafefed590fae5693552bba9794a9df68371cc", size = 179948, upload-time = "2026-07-17T22:50:28.521Z" },
-    { url = "https://files.pythonhosted.org/packages/35/25/9956b2d5e0529d5d23924f21bba1440d4c5c88a562e4f08550871ffa97a7/websockets-16.1.1-cp314-cp314t-macosx_10_15_universal2.whl", hash = "sha256:0ffd3031ea8bda8d61762e84220186105ba3b748b3c8da2ae4f7816fac03e573", size = 179963, upload-time = "2026-07-17T22:50:29.982Z" },
-    { url = "https://files.pythonhosted.org/packages/17/06/55ffc976c488b6aee9ea05761ff7c4e88e7c1fd82818c8ca7b556ad2f90c/websockets-16.1.1-cp314-cp314t-macosx_10_15_x86_64.whl", hash = "sha256:84a2cef8deffbd9ab8ee0ea546a2a6a7030c28f44e6cdd4547dbfeb489eb8999", size = 177497, upload-time = "2026-07-17T22:50:31.396Z" },
-    { url = "https://files.pythonhosted.org/packages/0c/e8/f7dac2e980bacc92bdc26cebae4ae4d50cae5380732c50980598fc0bbae4/websockets-16.1.1-cp314-cp314t-macosx_11_0_arm64.whl", hash = "sha256:3df13f73af9b3b38ab1195eb299ecb67a4330c911c97ae04043ff74085728abe", size = 177698, upload-time = "2026-07-17T22:50:32.829Z" },
-    { url = "https://files.pythonhosted.org/packages/b2/39/26762f734113e22da2b942c3aca85798e0c0405d64c256549540ff31e5a1/websockets-16.1.1-cp314-cp314t-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl", hash = "sha256:23253dd5bcae3f9aaee0a1d30967a8dbd52e5d3cff93a2e5b84df57b77d4750d", size = 187561, upload-time = "2026-07-17T22:50:34.24Z" },
-    { url = "https://files.pythonhosted.org/packages/11/94/c3f330851806b9b02138b774d593478323e73c99238681b4b93efe64e02d/websockets-16.1.1-cp314-cp314t-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:9c1c5705e314449e3308872fe084b8571ce078ee4fc55a98a769bdefe5917392", size = 188732, upload-time = "2026-07-17T22:50:36.088Z" },
-    { url = "https://files.pythonhosted.org/packages/d1/f2/eb2c450f052de334ae33cf200ece6e87b0e14d186807074e4eb1cd2cdea2/websockets-16.1.1-cp314-cp314t-manylinux2014_armv7l.manylinux_2_17_armv7l.manylinux_2_31_armv7l.whl", hash = "sha256:69e52d175a0a7d1e13b4b67ad41c560b7d98e8c6f6126eb0bda496c784faf8c7", size = 190872, upload-time = "2026-07-17T22:50:38.008Z" },
-    { url = "https://files.pythonhosted.org/packages/70/31/2ac8cecf3a74f7fed9132129fc3d90b3998a1554570c11a69b2a8c20332d/websockets-16.1.1-cp314-cp314t-manylinux2014_ppc64le.manylinux_2_17_ppc64le.manylinux_2_28_ppc64le.whl", hash = "sha256:1f79c89b5eb034d1722938a891916582f8f7f503f58ca22518a63c3f2cd18499", size = 189305, upload-time = "2026-07-17T22:50:39.53Z" },
-    { url = "https://files.pythonhosted.org/packages/6a/cf/8ab19650d3c0d4562c92e70ab47c257c4aa5c6a713ed87fe63766b31fefc/websockets-16.1.1-cp314-cp314t-manylinux2014_s390x.manylinux_2_17_s390x.manylinux_2_28_s390x.whl", hash = "sha256:39f2a024af5c345ffe8fcf1ee18c049c024c94df393bb09b044a6917c77bde43", size = 188033, upload-time = "2026-07-17T22:50:40.912Z" },
-    { url = "https://files.pythonhosted.org/packages/66/d7/a49a38a6127a4acb134fb1912b215d900cc657605cff32445bf519f3acc4/websockets-16.1.1-cp314-cp314t-manylinux_2_31_riscv64.manylinux_2_39_riscv64.whl", hash = "sha256:952303a7318d4cbe1011400839bb2051c9f84fa0a35923267f5daba34b15d458", size = 185748, upload-time = "2026-07-17T22:50:42.559Z" },
-    { url = "https://files.pythonhosted.org/packages/95/3e/ad1fa40388c7f2e0bb2c7930d0090b6c5498594bd1cdaec18864df3d9e97/websockets-16.1.1-cp314-cp314t-musllinux_1_2_aarch64.whl", hash = "sha256:249116b4a76063d930a46391ad56e135c286e4562a18309029fc2c73f4ed4c62", size = 188285, upload-time = "2026-07-17T22:50:43.974Z" },
-    { url = "https://files.pythonhosted.org/packages/35/b8/d5db28ca264b9104f82196f92dc8843e35fd391f763d42e4ad358f5bc97e/websockets-16.1.1-cp314-cp314t-musllinux_1_2_armv7l.whl", hash = "sha256:61922544a0587a13fd3f53e4c0e5e606510c7b0d9d22c8444e5fae22a06b38cb", size = 186777, upload-time = "2026-07-17T22:50:45.474Z" },
-    { url = "https://files.pythonhosted.org/packages/42/9c/726cb39d0cc43ae848dce4aa2acb04eecc6738b1264ec6d700bf6bcfb9f8/websockets-16.1.1-cp314-cp314t-musllinux_1_2_ppc64le.whl", hash = "sha256:46dcaa042cd1de6c59e7d9269fa63ff7572b6df40510600b678f0826b3c7af51", size = 188682, upload-time = "2026-07-17T22:50:46.973Z" },
-    { url = "https://files.pythonhosted.org/packages/be/c7/1168704de8c2dd483edabe4a22cbe4465dd8be8dd95561d214f9fe092871/websockets-16.1.1-cp314-cp314t-musllinux_1_2_riscv64.whl", hash = "sha256:38565aca3e01ea8734e578fb2118dade0ecb0250533f29e22b8d1a7a196cf4d0", size = 186377, upload-time = "2026-07-17T22:50:48.413Z" },
-    { url = "https://files.pythonhosted.org/packages/ca/40/f9ff2d630ffce4e7dfea0b2288e1caf9ebbf9ff8a9ec9396136ce8b94935/websockets-16.1.1-cp314-cp314t-musllinux_1_2_s390x.whl", hash = "sha256:42f599f4d48c7e1a3338fdaac3acd075be3b3cf02d4b274f3bf2767aedd3d217", size = 187148, upload-time = "2026-07-17T22:50:49.845Z" },
-    { url = "https://files.pythonhosted.org/packages/b5/71/e177c8299f78d7cbe2d14df228643c10c70c0e86e108e092056bbcc16e46/websockets-16.1.1-cp314-cp314t-musllinux_1_2_x86_64.whl", hash = "sha256:dcc04fedf83effaeb9cce98abc9469bb1b42ef85f03e01c8c1f4438ef7555737", size = 187578, upload-time = "2026-07-17T22:50:51.619Z" },
-    { url = "https://files.pythonhosted.org/packages/49/b2/b6987faf330f5af5c787a2610124c2e8403d51724f9001ec4fff6311fe7a/websockets-16.1.1-cp314-cp314t-win32.whl", hash = "sha256:8483c2096363120eea8b07c06ae7304d520f686665fffd4811fad423930a65d7", size = 179729, upload-time = "2026-07-17T22:50:53.269Z" },
-    { url = "https://files.pythonhosted.org/packages/a2/6e/fbac6ed878dd362fbad7d415fa4f84d38e3e33fed8cde45c64e783acf826/websockets-16.1.1-cp314-cp314t-win_amd64.whl", hash = "sha256:bcce07e23e5769375158f5efdcdafa8d5cd014b93c6683865b840ed65b96f231", size = 180072, upload-time = "2026-07-17T22:50:54.969Z" },
-    { url = "https://files.pythonhosted.org/packages/e1/ed/71fea6e141590cafc40b14dc5943b0845606bee87bdb52a21b6a73eb4311/websockets-16.1.1-pp311-pypy311_pp73-macosx_10_15_x86_64.whl", hash = "sha256:820fb8450edddae3812fd58cbc08e2bf22812cb248ecb5f06dbb82119a56e869", size = 177185, upload-time = "2026-07-17T22:50:56.665Z" },
-    { url = "https://files.pythonhosted.org/packages/01/ec/00e7eeca200facf9266a83e4cbbf1bed0e67fba1d4d45031d3e5b3d81b5c/websockets-16.1.1-pp311-pypy311_pp73-macosx_11_0_arm64.whl", hash = "sha256:125f22dbefaf1554fea66fc83851490edb284ce4f501d37ffed2752f418332d9", size = 177459, upload-time = "2026-07-17T22:50:58.197Z" },
-    { url = "https://files.pythonhosted.org/packages/75/fd/5774c4b33f7c0d8f0c51809c8b3a93456c48e3543579262cfa64eb5f522e/websockets-16.1.1-pp311-pypy311_pp73-manylinux1_x86_64.manylinux_2_28_x86_64.manylinux_2_5_x86_64.whl", hash = "sha256:30bbe120437b5648a77d3519b7024ea09530e0b5b18d3698c5a0ae536fe0cc2e", size = 178294, upload-time = "2026-07-17T22:50:59.641Z" },
-    { url = "https://files.pythonhosted.org/packages/37/c3/48e2c03d2bd79bb45948841c592d24156312dd5f58cdf8f549febe652fb6/websockets-16.1.1-pp311-pypy311_pp73-manylinux2014_aarch64.manylinux_2_17_aarch64.manylinux_2_28_aarch64.whl", hash = "sha256:b6b9dadbef0cccd9f4c4ee96b08898afa73e26803bbe0f6aeb5bb12b0074206d", size = 179190, upload-time = "2026-07-17T22:51:01.129Z" },
-    { url = "https://files.pythonhosted.org/packages/2d/3f/73e511ecf2496ceac57dd4ed8388efe2bcf0769338a2dbf242c8366ae87e/websockets-16.1.1-pp311-pypy311_pp73-win_amd64.whl", hash = "sha256:56cd5fc4f10a9ea8aa0804bddb7b42506cf9e136046f3b4c27de8fec9e2ecba5", size = 180330, upload-time = "2026-07-17T22:51:02.603Z" },
-    { url = "https://files.pythonhosted.org/packages/be/4d/2d0d67834092e354d2b0498f014a41249a89556bc406cf86f3e1557bb463/websockets-16.1.1-py3-none-any.whl", hash = "sha256:6abbd3e82c731c8e531714466acd5d87b5e88ac3243465337ba71d68e23ae7e3", size = 173814, upload-time = "2026-07-17T22:51:04.184Z" },
-]
-
 [[package]]
 name = "websockets"
 version = "17.0"
 source = { registry = "https://pypi.org/simple" }
-resolution-markers = [
-    "python_full_version >= '3.15'",
-    "python_full_version >= '3.12' and python_full_version < '3.15'",
-    "python_full_version == '3.11.*'",
-]
 sdist = { url = "https://files.pythonhosted.org/packages/da/ea/c0f7924f7ccf005d6ad1f829971762ae751727497d6db1977ba5a635314f/websockets-17.0.tar.gz", hash = "sha256:6bbe83c4ef52a7533d2d8c6a3512b93722fd0db6bc6bc638d45edd49ef201444", size = 183456, upload-time = "2026-07-29T18:07:16.726Z" }
 wheels = [
     { url = "https://files.pythonhosted.org/packages/04/66/1fa9cd9c0e2e77f74c5b9391f5e154b939efbf9695eb5e5bb72e1d993669/websockets-17.0-cp311-cp311-macosx_10_9_universal2.whl", hash = "sha256:ddd0444e942d1f42ea2ab5c38f6f9dddfd6782a5bda0a29e210b414dda7e3636", size = 212719, upload-time = "2026-07-29T18:04:23.164Z" },

```
