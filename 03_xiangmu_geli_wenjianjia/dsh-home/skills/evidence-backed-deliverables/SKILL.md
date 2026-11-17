---
name: evidence-backed-deliverables
description: Prove deliverables with re-runnable probes, not prose.
version: 0.1.0
author: Teknium (teknium1), Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [evidence, deliverables, probes, verification, kanban, reporting]
    related_skills: [hermes-wf-kanban-orchestration, unattended-agent-execution]
---

# Evidence-Backed Deliverables

When a task's value is the **numbers in it** (repo probe, market scan, audit, inventory, benchmark), the deliverable must be reproducible by a third party: a committed script that regenerates the artifact, an artifact that contains that script's verbatim stdout, and prose that quotes numbers **from the artifact by line reference** instead of retyping them. This skill does not cover code changes (use TDD) or writing with no data.

## When to Use

- A card/task says 落盘 / 探测 / 盘点 / 摸底 / 审计 / 统计 / 扫描 and the output is counts, sizes, prices, or rates
- A downstream card or a human will consume the numbers and may challenge them
- You must prove "this is real data, not a plausible guess"
- You are the reviewer deciding whether a worker's numbers are real

Don't use for: normal source edits, docs with no measurements, or anything where the live query is impossible — say "拿不到" instead of producing a number-shaped artifact.

## Prerequisites

- A git repo where the artifact and the script can both be committed (one commit per card)
- `python` on PATH (on Windows prefer the project venv: `./venv/Scripts/python.exe`)
- A writable scratch dir **outside** the repo, addressed with a native path (`<scratch>/stdout.txt`)

## How to Run

```bash
python scripts/tmp_probe_<topic>.py > <scratch>/stdout.txt 2> <scratch>/stderr.txt
printf 'EXIT=%s STDERR_BYTES=%s OUT_BYTES=%s\n' "$?" "$(wc -c < <scratch>/stderr.txt)" "$(wc -c < <artifact>)"
```

Never generate the artifact with `python -c` or a heredoc when the run is unattended — see `unattended-agent-execution`.

## Quick Reference

| Need | Command |
|---|---|
| Run probe | `python scripts/tmp_probe_<topic>.py` |
| Gate 1: ran clean | `echo EXIT=$?` plus `wc -c < <scratch>/stderr.txt` (must be 0) |
| Gate 2: artifact non-empty | `wc -l -c <artifact>` |
| Gate 3: verbatim quote | extract the fenced block by line numbers, `diff` against stdout, must be empty |
| Gate 4: no hedging words | `grep -c -E '应该|预期|大概|估计' <artifact>` → 0 (scope to your prose) |
| Gate 5: no secrets | `grep -n -E 'cookie|token|password|BDUSS' <artifact>` → 0 |
| Prove bytes are committed | `git hash-object <artifact>` vs `git rev-parse HEAD:<artifact>` |
| Fingerprint | `sha256sum scripts/tmp_probe_<topic>.py <artifact>` |

## Procedure

1. **Write the probe as a file.** `scripts/tmp_probe_<topic>.py`, pure file, no shell interpolation. Completion: `python <script>` exits 0 from a clean shell and `python -m py_compile <script>` is silent.
2. **Make the script write its own artifact**, not just print. Artifact structure: metadata table (`卡片`, `执行命令`, `执行时间`, `仓库根`, `退出码`) → fenced `text` block containing the script's stdout **verbatim** → summary section with the totals. Completion: the file exists and `grep -n '^```' <artifact>` returns exactly two fence lines for that block.
3. **Print the success marker only after the write succeeds** (`[OK] 真实输出已落盘: <path> (<bytes>)`). Completion: the marker is the last stdout line and carries the real byte count.
4. **Run once, capture, gate.** Completion: `EXIT=0`, stderr 0 bytes, `wc -l -c` non-zero; those three numbers go into your report.
5. **Prove the quote is verbatim.** Extract the fence body by line numbers and `diff` it against this run's stdout (strip `\r` first). Completion: `diff` prints nothing.
6. **Hash and record.** `sha256sum` both files and put the hashes in the governance log line. Completion: two 64-hex hashes recorded.
7. **Quote numbers only from the artifact, with line refs** (`文件总数 18606 / 376.60 MB（L28-29）`). Completion: every number in your prose traces to a line you can show.
8. **One commit** — script + artifact + governance log line — with the card id in the message. Completion: `git show --name-only <sha>` lists only your files.

### Reviewer variant (independent re-run)

1. Snapshot the committed artifact to scratch.
2. Run the script yourself (it overwrites the artifact) — record EXIT, stderr bytes, stdout lines.
3. Extract and diff the **committed snapshot's** fenced block against your stdout.
4. Restore the artifact from the snapshot; confirm byte identity: `git hash-object` == `git rev-parse HEAD:<artifact>`.
5. Report each check as command → real output, never "looks fine".

## Pitfalls

- **Numbers from a different run than the artifact.** Real incident: the probe ran three times; the committed report came from run 3 (18606 files / 376.60 MB) while the handoff narrative quoted run 1 (18582 / 370.86 MB). Both were real, the pairing was broken → reviewer rejected. Rule: after any re-run, re-read the artifact and re-quote; never carry numbers across runs.
- **The probe overwrites its own artifact.** Re-running to "check" clobbers the committed file. Snapshot first, restore after, verify with `git hash-object`.
- **`git checkout --` changes the byte count without changing content.** With `core.autocrlf=true` a restored LF file becomes CRLF (+1 byte per line; observed 29041 → 29402). Compare hashes, not `wc -c`, before declaring corruption.
- **`$TMPDIR` is `/tmp` in git-bash and native tools cannot read it.** Redirect to an explicit native scratch path, or `read_file` reports "File not found".
- **Forbidden-word grep hits quoted log lines.** A hit for `应该/预期` inside a quoted governance-log excerpt is not your prose; scope the grep or subtract the quoted lines explicitly.
- **`open(..., "w")` without `encoding="utf-8", newline="\n"`** produces mixed line endings that break later `diff`/`hash-object` comparisons.
- **「我们解出来了」的结论，先查变换参数是否跨样本恒定。** 正确的逆变换只有一个参数（一把 XOR key、一个口令、一本字典），它必须在每个样本上都相同。若是「每个文件算出的 key 都不一样」，那不是解密而是**在凑目标魔数**（`0x07^0x45='B'`、`0x08^0x45='M'` 这类巧合）：真 key 恒定，凑出来的必然逐样本漂移。两条独立判据：① ≥10 个样本必须解出同一个 key；② 至少一个样本能被真正的解析器（Pillow / zlib / 格式库）打开并读出尺寸，且**头部自述的长度字段与实际文件大小吻合**（一个声明 3.1 GB 的 BMP 而文件只有 57 KB，就是凑魔数）。两条都过不了就写「未解出 + 卡在哪」，不要写 ✅。
- **「恢复了 N 个文件」按内容验收，不按文件数验收。** 产物目录里文件齐全、测试全绿、每个文件都能 `PIL.verify()` 通过，仍然可能是假成功：恢复流水线的重组步骤只做了 `read()`+`concat`，**从没调用变换函数**；`verified = verify(...)` 算出来之后被丢弃，不管 True/False 都落盘计 success。于是加密原文被改了扩展名丢进 `recovered/`。

  三条独立探针，任一条不过就是假成功：

  ```python
  # ① 产物头部是否仍是输入密文的魔数（V2 微信 .dat 是 07 08 56 32 08 07）
  [f for f in Path('out').rglob('*') if f.is_file() and f.read_bytes()[:6] == bytes([7,8,86,50,8,7])]
  # ② 产物字节数是否与源文件 100% 相等 —— 相等 = 原样复制，不是解密
  # ③ 每个声称成功的文件都用真解析器打开并读出尺寸（不能只抽样前 3 个）
  ```

  还要防**「明文直拷混进解密成果」**：源文件本来就是明文（`.jpg` 头 `ff d8 ff`）时被复制过去，`PIL` 当然打得开，但这证明的是源文件没加密，与解密能力无关。统计必须分 `transformed / copied_plain / failed(reason)` 三类，笼统一个 `recovered` 数字就是误导。

  查链路断点只需两行：`grep -n "<变换类名>" <流水线模块>` 看变换函数是否真被调用；抽一个样本从头跑到尾看它有没有经过变换。
- **验收标准里的成功率下限会逼出造假。** 给一条「≥80% 成功率」而达成它所需的关键依赖（密钥 / 凭证 / 模型 / 网络）当前并不存在时，worker 面前只有两条路：如实报 0% 或伪造。多数会选伪造，且伪造形态看起来很像真的（拷贝计数、凑魔数、样本挑好的报）。

  正确写法是**把不可达的成功率换成禁止性断言 + 诚实分类计数**：

  | 别写 | 改成 |
  |---|---|
  | 恢复率 ≥ 80% | 产出目录中头部为输入密文魔数的文件数 **必须为 0** |
  | 转写准确率 ≥ 95% | 无样本时写「未能实测」，有样本时贴逐条对照 |
  | 全部通过 | `transformed / copied_plain / failed(reason)` 三段计数，每个 failed 带原因 |

  再加一条**有依赖时必须真跑**的用例：mock 一个合法密钥/凭证，证明通路本身是通的（`verified=True`），这样「当前 0 成功」和「实现根本不会解密」才能区分开。做不到就写「未能实测」，0 也可以交，编造不行。
- **Don't rewrite history in the governance log.** Append a rule-level correction ("今后以 artifact 的 §0 元信息为准，不再手抄数字") instead of editing earlier lines.


## Verification

- Re-run from the committed tree: `EXIT=0`, stderr 0 bytes, artifact byte-identical (`git hash-object` == HEAD blob)
- Fence body vs stdout `diff` empty
- Both hashes stable across two runs
- `git show --name-only` shows only script + artifact + governance log
