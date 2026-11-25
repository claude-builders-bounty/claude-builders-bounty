# 无人值守交接：让工作流自己跑一夜

用户说「我睡觉了，你们跑好流程」时，按本清单逐项确认。**默认配置撑不过一夜** ——
这不是配置错误，是默认值是按「有人看着」设计的。

## 一、两个默认值必须先改，否则半夜就空转

### 1. `WF_BLOCKED_MAX_RECOVER`（默认 3）—— 最致命

`blocked_recovery.py` 每卡自动恢复有硬上限，用完就标「已交人工」并不再动它。
上游不稳定时 worker 每几分钟失败一次，**卡数 × 3 次恢复在半小时内就会全部耗尽**，
之后整夜空转：`blocked` 越积越多、`dispatch.log` 依然每分钟一行、看起来「在跑」。

无人值守过夜要放到 **50~100**（`config.env` 加 `WF_BLOCKED_MAX_RECOVER="80"`），
配合 `WF_BLOCKED_COOLDOWN="60"`。

**验证不能只看配置写了没**，要证明程序真读到了 —— 导入模块读常量：

```python
import importlib.util
spec = importlib.util.spec_from_file_location("br", ".../blocked_recovery.py")
m = importlib.util.module_from_spec(spec)
try: spec.loader.exec_module(m)
except SystemExit: pass
print(m.MAX_RECOVER, m.COOLDOWN)      # 必须打出新值
```

### 2. `WF_AGENT_TIMEOUT_SEC`（默认 7200）—— 并发=1 时的隐形炸弹

`WF_MAX_CONCURRENT=1` 时，一个卡死的 worker 会**占满唯一的并发位**，`WF_AGENT_TIMEOUT_SEC`
就是整个队列停摆的上限。7200 秒 = 两小时什么都没发生。无人值守时放到 **1800**。

> 注意这与「进度感知超时」不冲突：墙钟上限只是兜底，真正判活靠上游请求日志有没有新行。

## 二、机器不会睡过去

主机休眠会静默掐断整夜。**交接前实测，不要假设**：

```python
import subprocess, re
for sub, name in (("STANDBYIDLE","系统睡眠"), ("HIBERNATEIDLE","休眠")):
    t = subprocess.run(["powercfg","/query","SCHEME_CURRENT","SUB_SLEEP",sub],
                       capture_output=True).stdout.decode("gbk", errors="replace")
    secs = dict((k, int(v,16)) for k,v in
                re.findall(r"当前(交流|直流)电源设置索引:\s*(0x[0-9a-f]+)", t))
    print(name, secs)      # AC/DC 都是 0 = 永不休眠
```

`powercfg` 输出是 GBK，直接管道给 grep 会得到 `Binary file matches` 而不是内容 —— 用 Python
按 `gbk` 解码再正则。

## 三、三个哨兵必须同时活着

缺任一个，夜间各有一类卡永久停摆：

| 哨兵 | 建议间隔 | 缺了会怎样 |
|---|---|---|
| 自动派单 | 1 分钟 | 什么都不派 |
| 受阻卡自动恢复 | 2 分钟 | 失败卡永久 blocked，队列逐渐枯竭 |
| 协调者验收 | 2 分钟 | `review` 队列堆积，`done` 永远不涨 |

逐个确认 `enabled=True` 且 `last=ok`，**不要只看「任务存在」**。

## 四、交接前把「今晚会怎样」讲清楚

用户睡觉前不该再收到一堆排查细节，只交代三件事：

1. **循环是什么形态** —— 派单 → 执行 → 失败 → 自动恢复 → 再派，卡不会丢。
2. **改了什么、为什么** —— 每条一句，附实测依据（尤其「默认值撑不过一夜」这类）。
3. **明早看哪三行判定它有没有干活** —— 给出 `baseline` 数字，并明确指出**唯一需要叫醒你的信号**
   （通常是 `blocked` 攒起来不降 = 恢复哨兵挂了；`todo` 上涨是 worker 在拆子卡，正常）。

## 五、夜间唯一可信的进度判据是不同状态的变化方向

| 指标 | 健康 | 故障 |
|---|---|---|
| `done` 上涨 | 真出活了 | 不动 = 一张都没验收通过 |
| `blocked` 下降或持平 | 恢复哨兵在工作 | 持续上涨不回落 = 恢复哨兵挂了 |
| `todo` 上涨 | worker 在拆子卡，**正常** | — |
| `running` 长期 = 1 且不换卡 | — | worker 卡死，查 `WF_AGENT_TIMEOUT_SEC` 与上游请求日志 |

不要把 `todo` 上涨误报成故障 —— 它恰恰是 worker 真在拆卡的证据。

## 六、早间盘点：「汇报运行状况」的固定动作

用户一早问「汇报运行状况」时，**不要凭印象或昨天的结论答**。按下面四个数字取证，
一次把「真干了多少活」和「环境又烂了多少」分开说清楚。

```python
# ① 看板差值：done 涨了多少、archived 为何涨
SELECT status, COUNT(*) FROM tasks GROUP BY status;
# ② 真提交：拿真实卡号去对，不数文件数
git log --since="12:00" --oneline | grep -c "t_"
# ③ 今日完成卡（completed_at 可能为 NULL，别拿它做唯一判据）
SELECT id, completed_at FROM tasks WHERE status='done' ORDER BY completed_at DESC LIMIT 6;
# ④ 进程 + 仓库干净度
powershell -NoProfile -Command "@(Get-CimInstance Win32_Process -Filter \"Name='claude.exe'\").Count"
git status --porcelain -uall | wc -l
```

**`archived` 上涨不是坏事，要分开看。** 它多半是「打回满 N 次自动归档」在生效（设计如此），
但如果一批卡是在**已知系统性 bug 期间**被归档的，它们值得在根因修完后复活重跑一次 ——
把「归档原因」和「归档时间」一起报告给用户，让他决定。

**无人值守一夜必现的三类回潮，逐一核：**

| 回潮 | 一眼判据 | 处置 |
|---|---|---|
| 垃圾脚本 | `git status --porcelain -uall \| wc -l` 大幅上升 | 跑环境守卫；非零就补规则（按目录结构性判据，不按名字）|
| 追加型文档被截断/被删 | 行数骤降或文件不存在 | 从快照恢复；文件不存在也要恢复，不是只有截断才管 |
| 卡面与交付纪律矛盾 | worker 反复报「无 Shell / 无法自行提交」 | 查卡面有没有「不要提交」类反向指令 |

**根因修复不会自动生效到已经在跑的 worker。** 改派单参数后，拿 `started_at` 早于改动时间的卡
的自述去判断「补丁失效」是错的 —— 等新一批 worker 再判。汇报时要把这两种行为分开讲。

**汇报的形态**（用户要的是结论，不是流水账）：先给看板差值表（`done` 前→后、`archived` 前→后），
再列「这轮新暴露并修掉的问题」（每条一句根因 + 一句实测证据），最后给「现在卡在哪」+
一个需要用户拍板的开放问题。**不要把「修了管道」当成「出活了」报告。**
