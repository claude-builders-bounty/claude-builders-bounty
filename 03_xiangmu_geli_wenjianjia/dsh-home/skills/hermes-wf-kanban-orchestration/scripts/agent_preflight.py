#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
agent_preflight.py — hermes-wf 子员工环境自检
===============================================
在派单前把「会让子员工静默零产出」的环境问题一次性查出来。

用法:
    python agent_preflight.py                      # 常规自检
    python agent_preflight.py --fix                # 补缺失的 tools / 落盘规则
    python agent_preflight.py --quiet              # 只输出非 PASS
    python agent_preflight.py --dir D:/x/scripts/hermes-wf-<board>

默认配置路径 $HERMES_WF_DIR/config.env 或 D:/Ai/Agent/hermes/scripts/hermes-wf/config.env
退出码: 0 = 全绿; 1 = 有 FAIL

为什么需要它：任何一项红都会让 worker exit 0 却零产出，而哨兵日志照样 rc=0。
"""
import os, re, sys, json, subprocess, pathlib
from textwrap import dedent

WF_DIR = pathlib.Path(os.environ.get("HERMES_WF_DIR", r"D:/Ai/Agent/hermes/scripts/hermes-wf"))
if "--dir" in sys.argv:
    WF_DIR = pathlib.Path(sys.argv[sys.argv.index("--dir") + 1])
CONFIG = WF_DIR / "config.env"

REQUIRED_TOOLS = ["Read", "Grep", "Glob", "Bash", "Write", "Edit"]
LANDING_MARK = "## 落盘要求（全局硬规则"

LANDING_RULE = dedent("""\
## 落盘要求（全局硬规则，优先级高于后文任何「只读」措辞）

你有 `Write` / `Edit` / `Bash` 权限，并且**必须使用它们**：

1. 任务卡点名了产出路径 → 必须用 `Write` 工具真正写进该文件。
   **只把内容输出在对话里 = 没完成任务**，协调者会判定「零产出」并打回。
2. 任务卡没指定路径 → 写到当前工作目录下语义最贴近的位置，
   并在最后的回复里报告**绝对路径**。
3. 「只读」的意思是「不要擅自改动与本卡无关的业务代码」，
   **不是**「什么都不能写」。你自己负责的交付物（文档/报告/测试/脚本）必须落盘。
4. 写完用 `Bash` 做一次存在性与体积自检（如 `ls -l <路径>`），把结果写进回复。
5. 不要修改工作目录之外的任何文件。

""")

results = []
def ok(i, d=""):    results.append(("PASS", i, d))
def fail(i, d=""):  results.append(("FAIL", i, d))
def warn(i, d=""):  results.append(("WARN", i, d))


def parse_env(path):
    env = {}
    if not path.is_file():
        return env
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def split_fm(text):
    m = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n", text, re.S)
    return (m.group(1), text[m.end():]) if m else (None, text)


def get_tools(fm):
    m = re.search(r"^tools:\s*\[(.*?)\]\s*$", fm or "", re.M)
    return [x.strip().strip('"\'') for x in m.group(1).split(",") if x.strip()] if m else None


# ── 1. 环境变量 / settings ──────────────────────────────────────
cfg_dir = os.environ.get("CLAUDE_CONFIG_DIR", "")
if cfg_dir and pathlib.Path(cfg_dir).is_dir():
    ok("CLAUDE_CONFIG_DIR", cfg_dir)
else:
    fail("CLAUDE_CONFIG_DIR", f"未设置或目录不存在: {cfg_dir!r}")

settings = pathlib.Path(cfg_dir) / "settings.json" if cfg_dir else None
if settings and settings.is_file():
    try:
        s = json.loads(settings.read_text(encoding="utf-8", errors="ignore"))
        mode = s.get("permissions", {}).get("defaultMode", "")
        (ok if mode in ("bypassPermissions", "acceptEdits") else warn)(
            "permissions.defaultMode", mode or "(未设)")
        tok = s.get("env", {}).get("CLAUDE_CODE_MAX_OUTPUT_TOKENS")
        (ok if tok else warn)("CLAUDE_CODE_MAX_OUTPUT_TOKENS", tok or "未设（dispatch 会补 32000）")
    except Exception as e:
        fail("settings.json 解析", str(e))
else:
    fail("settings.json", "不存在")

# ── 2. claude 可执行 ────────────────────────────────────────────
try:
    r = subprocess.run(["where", "claude"], capture_output=True, text=True, timeout=15)
    (ok if r.returncode == 0 and r.stdout.strip() else fail)(
        "claude 在 PATH", (r.stdout.strip().splitlines() or ["未找到"])[0])
except Exception as e:
    fail("claude 在 PATH", str(e))

# ── 3/4. agent 目录 + 逐个体检 ──────────────────────────────────
agents_dir = pathlib.Path(cfg_dir) / "agents" if cfg_dir else None
agent_files = sorted(agents_dir.glob("cc-*.md")) if agents_dir and agents_dir.is_dir() else []
if agent_files:
    ok("cc-* agent 数量", f"{len(agent_files)} 个")
else:
    fail("cc-* agent 数量", "0 个（生效目录里一个都找不到 → 哨兵永远派不出）")

missing_tools, missing_rule, bad_fm, fixed = [], [], [], 0
for p in agent_files:
    raw = p.read_text(encoding="utf-8", errors="ignore")
    fm, body = split_fm(raw)
    if fm is None:
        bad_fm.append(p.name); continue
    tools = get_tools(fm) or []
    lack = [t for t in REQUIRED_TOOLS if t not in tools]
    need_rule = LANDING_MARK not in body

    if (lack or need_rule) and "--fix" in sys.argv:
        if lack:
            fm = re.sub(r"^tools:\s*\[.*?\]\s*$",
                        "tools: [" + ", ".join(f'"{t}"' for t in tools + lack) + "]",
                        fm, flags=re.M)
        if need_rule:
            body = LANDING_RULE + body
        p.write_text(f"---\n{fm}\n---\n{body}", encoding="utf-8")
        fixed += 1
        lack, need_rule = [], False

    if lack:        missing_tools.append(f"{p.stem}(缺 {','.join(lack)})")
    if need_rule:   missing_rule.append(p.stem)

(ok if not bad_fm else fail)("frontmatter 解析", ", ".join(bad_fm) or f"{len(agent_files)} 个正常")
(ok if not missing_tools else fail)("tools 权限", "; ".join(missing_tools) or "全部含 " + "/".join(REQUIRED_TOOLS))
(ok if not missing_rule else fail)("落盘规则", f"{len(missing_rule)} 个缺: {', '.join(missing_rule[:5])}" if missing_rule else "全部已注入")
if fixed:
    warn("--fix 自动修复", f"{fixed} 个文件")

# ── 5. 备份区同名 ──────────────────────────────────────────────
backup = pathlib.Path(os.path.expanduser("~")).resolve()
bdir = pathlib.Path(cfg_dir).resolve() if cfg_dir else None
if bdir != backup:
    ba = backup / ".claude" / "agents"
    if ba.is_dir():
        a = {p.name for p in agent_files}
        b = {p.name for p in ba.glob("cc-*.md")}
        (ok if a == b else warn)("备份区一致性", f"仅权威={a-b} 仅备份={b-a}" if a != b else f"{len(b)} 个同名")

# ── 6. config.env ──────────────────────────────────────────────
env = parse_env(CONFIG)
if not env:
    fail("config.env", str(CONFIG))
else:
    ok("config.env", f"{len(env)} 项")
    for k in ("WF_BOARD", "WF_AGENT_PREFIX"):
        (ok if env.get(k) else fail)(k, env.get(k) or "未设置")
    repo = pathlib.Path(env.get("WF_REPO", ""))
    (ok if (repo / ".git").exists() else fail)("WF_REPO 是 git 仓库", str(repo))

    dirs = {}
    for item in env.get("WF_AGENT_DIRS", "").split(","):
        if "=" in item:
            a, d = item.split("=", 1)
            dirs[a.strip()] = d.strip()
    names = {p.stem for p in agent_files}
    unmapped = sorted(names - set(dirs))
    (ok if not unmapped else warn)("目录映射覆盖",
        f"{len(unmapped)} 个落仓库根: {', '.join(unmapped[:5])}" if unmapped else f"{len(dirs)} 条全覆盖")
    missing = sorted({d for d in dirs.values() if not (repo / d).is_dir()})
    (ok if not missing else fail)("映射目录存在", ", ".join(missing) or f"{len(set(dirs.values()))} 个目录")

    at = env.get("WF_CLAUDE_ARGS", "")
    lack_at = [t for t in ("Bash", "Read", "Write", "Edit", "Grep", "Glob") if t not in at]
    (ok if not lack_at else fail)("WF_CLAUDE_ARGS 工具", f"缺 {','.join(lack_at)}" if lack_at else "齐全（必须逗号分隔）")

# ── 7. 哨兵 cron ───────────────────────────────────────────────
try:
    r = subprocess.run(["hermes", "cron", "list"], capture_output=True, text=True,
                       timeout=30, encoding="utf-8", errors="ignore")
    board = env.get("WF_BOARD", "")
    (ok if (board and board in r.stdout) or "哨兵" in r.stdout else fail)(
        "派单哨兵 cron", "未找到" )
except Exception as e:
    warn("派单哨兵 cron", f"查询失败: {e}")

# ── 输出 ───────────────────────────────────────────────────────
quiet = "--quiet" in sys.argv
icon = {"PASS": "✅", "FAIL": "❌", "WARN": "⚠️ "}
print("=" * 78)
print("  hermes-wf 子员工环境自检   " + str(WF_DIR))
print("=" * 78)
n_fail = 0
for lvl, item, detail in results:
    if lvl == "PASS" and quiet:
        continue
    n_fail += lvl == "FAIL"
    print(f"{icon[lvl]} {item:28s} {detail}")
print("=" * 78)
print(f"  PASS {sum(1 for x in results if x[0]=='PASS')} | "
      f"WARN {sum(1 for x in results if x[0]=='WARN')} | FAIL {n_fail}")
print("=" * 78)
sys.exit(1 if n_fail else 0)
