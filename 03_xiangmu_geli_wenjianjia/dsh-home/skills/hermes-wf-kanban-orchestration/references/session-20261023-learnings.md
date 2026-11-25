# 2026-10-23 会话关键学习补录

本文件记录 wechat_recovery 项目（P0-P7）实战中新发现的关键坑点与修法，作为 `dispatch-safety.md` 与 `watchdog-implementation.md` 的补充。

---

## 1. API 契约不一致（Worker 实现与 Spec 脱节）

**现象**：P2 worker 实现了 `FileRecovery.recover_all()` 但 Spec（`ARCHITECTURE.md` / `API_CONTRACTS.md`）要求 `FileRecoveryEngine.recover(scan_result, decryptor, output_dir)`；`DatDecryptor.decrypt_to_bytes()` vs Spec 的 `decrypt(dat_path, output_dir)`。测试全绿、文件存在，但下游（P8/P3）无法调用。

**修法**：
- 审查必须逐项对照 `API_CONTRACTS.md` / `ARCHITECTURE.md` 检查类名、方法签名、返回类型、异常体系。
- 不匹配即 `REQUEST_CHANGES`，要求重写或补兼容层。
- 卡正文需写明「必须实现 Spec 定义的公共 API，命名/签名/返回值严格对齐」。

---

## 2. 假成功第二层：产物是原始密文改扩展名

**现象**：P2 提交声称 "154 个文件已恢复"，实测 143 个 `.bin` 头部全是 `07 08 56 32`（V2 AES+XOR 魔数），字节数与源 `.dat` 完全一致，仅 11 个 `.jpg` 是源文件本来明文（纯复制）。

**根因**：`_reassemble_fragments()` 只做 `read()` 拼接，**从未调用 DatDecryptor**，`verified` 结果被丢弃。

**修法**：
- 解密失败记入 `failed` 列表，**绝不写文件**。
- 返回 `RecoveryReport(decrypted, copied_plain, failed, duplicate_skipped)` 四段结构，不再笼统叫 `recovered`。
- 成功率门槛（如 ≥80%）在本机不可达（V2 需 AES key 从微信内存提取），**不设门槛**，如实报真实解密数，0 也行但要写清 "缺 key"。

---

## 3. 验收必须真打开产物，不能只数文件

**铁律**：文件数、`pytest` 全绿、`PIL.verify()` 都能通过（源文件本来就没加密时），但 "恢复了 N 个" 实际 N 个都是改了扩展名的加密原文。

**查验方法（审查必跑，顺序不省）**：
```bash
# 1. 产物头部是否仍是输入密文的魔数（如 07 08 56 32 = V2 AES+XOR）
xxd output/**/*.bin | head -20
# 2. 产物字节数是否与源文件 100% 相等（说明只是改了扩展名）
stat -c '%s' src.dat output/**/*.bin | sort | uniq -c
# 3. 每个声称成功的文件是否都用真解析器打开过
for f in output/**/*; do
  case "$f" in
    *.jpg|*.png) python -c "from PIL import Image; Image.open('$f').verify()" ;;
    *.mp4|*.mkv) ffprobe -v error -show_entries format=duration '$f' ;;
    *.silk|*.wav) ffprobe -v error -show_entries format=duration '$f' ;;
  esac
done
```

**三档判定**：
- 文档写 ✅ 而实际 False → **REQUEST_CHANGES**，不讨论。
- 声称存在的目录 `exists=False` → REQUEST_CHANGES，要求改成 "待实测确认"。
- 只有 "真跑过、能贴出命令与输出" 才允许写 "实测"；否则只能写 "官方宣称 / 第三方来源 / 待实测"。做不到写 "未能实测" 不扣分，编造实测直接打回。
- **产物是原始密文改扩展名** → REQUEST_CHANGES，并要求 "失败不落盘、分类统计 decrypted/copied_plain/failed"。

---

## 4. 卡 running 但无 worker 进程 → 自动触发 review（兜底）

**现象**：系统重启/父进程 crash 导致 worker 死掉但卡留在 `running`，dispatch 守卫 ⑦ 从未执行（未捕获退出码）。事件表只有 `claimed`，无 `completed`/`request-review`；`git log` 有新提交但卡状态没变。

**修法**：新增 `stuck_task_fixer.py`（放在 `hermes-wf/` 目录）：
- 每 5 分钟 cron tick 检测 `status='running' AND 无 claude 进程` 的卡
- 有新提交（比对 HEAD 或工作区指纹）则自动 `hermes kanban request-review`
- 已加入 cron monitor 链路，防止 "假跑完" 卡死

---

## 5. 系统重启后的卡状态修正

**现象**：电脑自动关机重启会杀掉所有 claude 进程。看板仍显示 `running`、`worker_pid`、`claim_lock`。

**修正脚本**：
```python
import sqlite3, datetime
DB = r"D:\Ai\Agent\hermes\kanban\boards\<board>\kanban.db"
conn = sqlite3.connect(DB)
now = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
conn.execute("""UPDATE tasks SET status='ready', worker_pid=NULL, claim_lock=NULL,
                claim_expires=NULL, block_recurrences=0,
                consecutive_failures=0 WHERE id=?""", (tid,))
conn.commit()
```

不修会导致下一次派单时 reconciliation 冲突或双跑。

---

## 6. Cron 失效时手动派单是主流程降级路径，不是应急绕过

**现象**：NVIDIA API 402/429 导致 cron 报错停摆（`last_status=error`，`last_error=HTTP 402`）。

**操作**：
1. 确认无 claude 进程（`Get-Process -Name claude` 返回 0）
2. 卡状态为 `ready`（或手动改回 `ready`、清 `worker_pid`/`claim_lock`）
3. `FORCE_DISPATCH=1 ./dispatch_claude.sh <tid> <agent> "prompt"` 直接跑
4. 等 worker 跑完 → 协调层亲审 → `complete` / `request-changes`

**不要等 cron 修好才推进**。手动派单 + 协调层亲审是主流程的降级路径，不是应急绕过。

---

## 7. 串行派单防 429 是强制规则，不是建议

**现象**：通道限流时并行派单 = 自己制造 429，还会叠加双写同一 git 树风险。

**规则**：`Get-Process -Name claude` 返回 `0` 才派下一张。

**理由**：一张卡跑 20 分钟，排队也比四张卡全被 429 打回再重试快得多。"串行"不等于 "慢"。

---

## 8. Worker 方向性错误（方案本身是废的）是最贵的失效

**现象**：文件存在、测试能过、日志显示完成，但产物换机器就是废的（裸 PyInstaller 漏 38MB flet 客户端、flet==0.21.2 降级炸弹、frozen 态配置写临时目录）。

**对策**：协调层必须独立验证真实路径，不采信任何自述。

---

## 9. 实战验收清单（协调层亲审每张 done 卡必跑）

```bash
# 1. git 核验
git log --all --oneline --grep="<卡号>" | head -5
git show --stat HEAD
# 2. 文件域核验（没越界）
git show --name-only <sha>
# 3. 硬编码零容忍
grep -rn "wodwend\|wxid_\|4\.1\.0\.34" --include="*.py" core/ tests/ frontend/
# 4. 真实测试
python -m pytest tests/ -q
# 5. 文档声称的每条关键命令，挑真的跑
grep -n "✅" docs/*.md | head -30
# 6. 声称存在的文件/目录，挨个 ls
ls -la tests/asr/bench_cer.py docs/COMPATIBILITY.md
# 7. 声称的路径真能不能被发现
python -c "from utils.path_helper import find_wechat_data; print(find_wechat_data())"
# 8. 真打开产物
for f in output/**/*; do
  case "$f" in *.jpg) python -c "from PIL import Image; Image.open('$f').verify()" ;; esac
done
```

---

*Distilled from wechat_recovery project (2026-10-18 ~ 2026-10-23) — 9 cards, 5 review cycles, 1 auto-shutdown recovery, 1 cron 402 fallback.*