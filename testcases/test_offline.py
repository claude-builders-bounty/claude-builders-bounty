#!/usr/bin/env python3
"""Offline tests for the review logic (no network needed)."""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts"))
import importlib.util
spec = importlib.util.spec_from_file_location("review_pr", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "review_pr.py"))
rp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rp)

pr = {
    "title": "Add user login",
    "body": "Adds a login page with bcrypt hashing.",
    "html_url": "https://github.com/x/y/pull/1",
    "draft": False,
    "additions": 120,
    "deletions": 5,
    "base": {"ref": "main"},
    "head": {"ref": "feat/login"},
}
files = [
    {"filename": "app/login/page.tsx", "patch": "+ import { hash } from 'bcrypt'\n+ const token = process.env.SECRET\n+ password = \"hunter2\"\n+ const x = eval(input)\n+ console.log('debug')\n+ TODO: handle CSRF\n"},
    {"filename": "app/api/login/route.ts", "patch": "+ DROP TABLE users\n"},
    {"filename": "tests/login.test.tsx", "patch": "+ expect(1).toBe(1)\n"},
]
review = rp.build_review(pr, files)
print(review)
print("---")
assert "security: dynamic code execution" in review
assert "security: possible hardcoded credential" in review
assert "style: leftover debug output" in review
assert "security: destructive SQL without WHERE" in review
assert "No test files changed" not in review   # 因为有 tests/ 目录
print("offline tests passed")

# ---- 回归测试（凭据检测假阳性修复 + 补覆盖） ----

# 环境变量读取不应被误判为硬编码凭据
files_env = [
    {"filename": "app/config.py", "patch": "+ token = os.environ['API_TOKEN']\n"},
    {"filename": "app/config2.js", "patch": "+ const secret = process.env.SECRET\n"},
    {"filename": "app/config3.py", "patch": "+ api_key = os.getenv('KEY')\n"},
]
review_env = rp.build_review(pr, files_env)
assert "security: possible hardcoded credential" not in review_env, "env var reads should not be flagged"

# 真正硬编码的凭据仍应被抓到
files_hardcoded = [
    {"filename": "app/bad.py", "patch": "+ password = \"hunter2\"\n"},
]
review_bad = rp.build_review(pr, files_hardcoded)
assert "security: possible hardcoded credential" in review_bad

# TypeScript any 泄漏规则要有测试覆盖
files_any = [
    {"filename": "app/types.ts", "patch": "+ const x = value as any\n"},
]
review_any = rp.build_review(pr, files_any)
assert "style: TypeScript any leak" in review_any

# 无限循环规则要有测试覆盖
files_loop = [
    {"filename": "app/loop.js", "patch": "+ while (true) { run(); }\n"},
]
review_loop = rp.build_review(pr, files_loop)
assert "performance: unbounded loop" in review_loop

# ---- 第二轮回归测试（has_tests 假阳性 / doc-gap 扩展名 / env 边界 / patch null） ----

# has_tests 假阳性：文件名恰好含 "test" 子串但不是测试文件，应报"缺少测试"
for name in ("app/latest.ts", "app/api/testify.py", "src/contest.js"):
    r = rp.build_review(pr, [{"filename": name, "patch": "+ x = 1\n"}])
    assert "No test files changed" in r, f"{name} should be flagged as missing tests"

# 但真正的测试文件仍应被识别（后缀与目录两种写法）
for name in ("tests/login.test.tsx", "src/__tests__/app.spec.js", "test/util.test.py"):
    r = rp.build_review(pr, [{"filename": name, "patch": "+ expect(1).toBe(1)\n"}])
    assert "No test files changed" not in r, f"{name} should count as a test file"

# doc-gap 扩展名对齐：纯 .tsx 源码 PR 应报"无文档更新"（旧列表漏 .tsx）
r = rp.build_review(pr, [{"filename": "app/login/page.tsx", "patch": "+ const a = 1\n"}])
assert "No documentation updated" in r, "tsx-only PR should trigger doc gap"

# doc-gap 排除测试文件：纯 .test.tsx PR 不应报"无文档更新"
r = rp.build_review(pr, [{"filename": "app/login/page.test.tsx", "patch": "+ expect(1).toBe(1)\n"}])
assert "No documentation updated" not in r, "test-only PR should not trigger doc gap"

# env 读取边界：process.env['X']（不带点）也不该误报
r = rp.build_review(pr, [{"filename": "app/c.js", "patch": "+ const token = process.env['TOKEN']\n"}])
assert "security: possible hardcoded credential" not in r, "process.env['X'] is an env read"

# patch 键缺失或为 null（二进制文件）不应崩溃
rp.build_review(pr, [{"filename": "assets/logo.png"}])
rp.build_review(pr, [{"filename": "assets/logo.png", "patch": None}])

print("round-2 regression tests (has_tests/doc-gap/env-boundary/patch-null) passed")

# ---- 第三轮回归测试（验收四段式结构 + Confidence + 新版风险分类） ----

# 四段式标题必须逐字出现（bounty #4 验收：Summary / Identified risks /
# Improvement suggestions / Confidence score）
for heading in ("### Summary of changes", "### Identified risks",
                "### Improvement suggestions", "### Confidence score"):
    assert heading in review, f"missing section: {heading}"

# Confidence 必须是 Low / Medium / High 之一，且出现在独立加粗行
import re
m = re.search(r"### Confidence score\n+\*\*(Low|Medium|High)\*\*", review)
assert m, "confidence score line missing"

# 含 security 风险的 PR → High（当前样例 PR 含 eval 等 security finding）
assert m.group(1) == "High", f"security risk should give High, got {m.group(1)}"

# 无风险的小 PR → Medium
pr_small = dict(pr, additions=10)
r_small = rp.build_review(pr_small, [{"filename": "app/a.py", "patch": "+ x = 1\n"}])
m = re.search(r"### Confidence score\n+\*\*(Low|Medium|High)\*\*", r_small)
assert m and m.group(1) == "Medium", f"small clean PR should be Medium, got {m and m.group(1)}"

# 超大 diff（>40 文件或 >2000 行）→ Low
pr_big = dict(pr, additions=3000)
r_big = rp.build_review(pr_big, [{"filename": "a/b.py", "patch": "+ x = 1\n"}])
assert "**Low**" in r_big.split("### Confidence score")[1], "huge diff should be Low"

# 有测试覆盖但无风险 → 仍应 High（测试覆盖提升可信度）
r_tested = rp.build_review(pr_small, [{"filename": "tests/a.test.py", "patch": "+ expect(1).toBe(1)\n"}])
assert "**High**" in r_tested.split("### Confidence score")[1], "test coverage should give High"

# style/follow-up 类不应出现在 Identified risks（归入 Improvement suggestions）
assert "leftover debug output" not in review.split("### Identified risks")[1].split("### Improvement suggestions")[0], \
    "style findings must not appear under Identified risks"
assert "leftover debug output" in review.split("### Improvement suggestions")[1]

# security 类仍应在 Identified risks
assert "dynamic code execution" in review.split("### Identified risks")[1].split("### Improvement suggestions")[0]

print("round-3 regression tests (4-section layout / confidence / risk split) passed")
