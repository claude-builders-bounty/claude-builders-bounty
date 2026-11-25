# 上游限流纪律与 429 取证

适用于「限流代理 + 多 worker + 单一上游配额」这类链路（本机：Claude Code → cc-switch:15721 →
限流代理:15722 → NVIDIA）。目标是回答三个问题，且全部只用实测数据：
**是不是我们在打爆上游 / 是哪个会话在打爆 / 重试是缓解还是放大。**

## 0. 先记住一条

> **压力守恒。** 你能消灭的只是「客户端可见的失败」，不是「上游承受的压力」。
> 每一次「更聪明地重试」都等价于把 1 次请求变成 N 次，而真正的约束（单会话速率）一次都没被动到。

## 1. 健康度曲线：按 30 分钟桶看状态分布

`created_at` 是 **10 位秒级**（用位数分布自证，别凭印象当毫秒）：

```python
lens = collections.Counter(len(str(r[0])) for r in cur.execute("select created_at from proxy_request_logs"))
# {10: N} → 秒；出现 13 位才是毫秒
```

```sql
SELECT (created_at/1800)*1800 AS bucket,
       COUNT(*) AS tot,
       SUM(status_code=200) AS ok,
       SUM(status_code=429) AS e429,
       SUM(status_code>=500 AND status_code<600) AS e5xx
  FROM proxy_request_logs GROUP BY 1 ORDER BY 1;
```

**判读**：成功率 <50% 的桶就是事故桶；把事故桶的**请求总量**和健康桶对比 ——
若总量同时翻了 3~4 倍，病因是流量，不是上游。

## 2. 归因到会话：谁在打爆

会话 id 就是 Claude Code 的一次 worker 运行。**正常会话 5–14 RPM**，跑飞的是几十到上百。

```sql
SELECT substr(session_id,1,8) AS sid,
       MIN(created_at) AS t0, MAX(created_at) AS t1,
       COUNT(*) AS n,
       ROUND(COUNT(*)*60.0/(MAX(created_at)-MIN(created_at)+1), 1) AS rpm,
       SUM(status_code=200) AS ok
  FROM proxy_request_logs
 WHERE created_at > strftime('%s','now') - 7200
 GROUP BY sid HAVING n > 50 ORDER BY rpm DESC;
```

实测样例（同一小时内的多个会话）：正常 5–14 RPM / 100% 成功；
**107.8 RPM / 30% 成功**；暴风过后被排队压到 **1.5–1.7 RPM** —— 这三个数字分别是「病根」「发病」「假健康」。

## 3. 429 三问：速率 / key 冷却 / 鉴权

| 观测 | 结论 | 下一步 |
|---|---|---|
| 孤立单发（>5s 间隔，只发一次）即 429 | 账号/key 级**冷却** | 换 key，别降速重试 |
| `GET /v1/models` 仍 200 | key **有效** | 不要查权限/换 token |
| 换另一个 key 3/3 全 200 | 按 key 冷却已确认 | 上 key 池轮换 |
| 单发 200、连发才 429 | 真·速率上限 | 排队，不要重试 |

**陷阱：阶梯测速会自己骗自己。** 账号已处于冷却簇时，「10s 间隔首发就 429 / 3s 间隔全 200」
必然出现，读成「跟速率无关」就是反了。测上限必须在**冷账号**（静默 10 分钟以上）上做，
且只取「连续 N 发全 200」的那一档当上限，不要取单点。

## 4. 重试：占名额才算限流，否则是放大器

```python
# ✗ 放大器：进函数拿一次名额，重试不再排队
LIMITER.acquire()
for attempt in range(RETRY):
    r = post(...)
    if r.status_code != 429: break
    sleep(backoff)

# ✓ 限流：每个上游尝试都是一个名额
for attempt in range(RETRY):
    LIMITER.acquire()
    r = post(...)
    if r.status_code != 429: break
    cool_key_or_sleep(r.headers.get("Retry-After"))
```

**自检两个数**：

- `限流器显示 RPM` vs `日志里每分钟重试行数`。后者明显大于前者 ⇒ 出站被放大。
- 队列平均等待长期 `0.0s` 而上游仍 429 ⇒ 限流器形同虚设（上限被调高到从不触发）。

累计等待必须小于客户端超时（cc-switch `streaming_first_byte_timeout` / `non_streaming_timeout`），
否则「等了 70 秒才拿 429」比立刻失败更糟：worker 被拖死、卡在 running 里白占并发位。

## 5. key 池轮换的正确形态

- 429 时**先换 key，再谈等待**；`Retry-After` 有值就按它冷却，缺省 45s、上限 300s。
- key 池只在内存，**永不写盘、永不打日志**；日志只用序号（`key#1`）与 provider 名。
- 全池都在冷却才 sleep，且 sleep 时长要封顶，避免把客户端超时吃满。

## 6. 闸门放错层：两个方向都会死

派单层的 RPM 闸门（「最近 60s 请求数 ≥ N 就不派单」）在这条链路上被证明两头都错：

| 方向 | 现象 | 后果 |
|---|---|---|
| 上限偏高 / 统计漏掉重试 | 闸门常绿 | 上游被打爆；单会话 107.8 RPM 时闸门照样放行 |
| 上限偏低 / 统计含在跑会话 | 闸门常红 | **新卡永远不派**，业务链整体饿死，日志每分钟一行看着像在工作 |

第二条的数值：上限 32、在跑 3 卡自身 81–162 RPM ⇒ 拒绝率接近 100%，10 张业务卡 22.4 小时 0 次尝试。

正确分层：**派单层只控并发（`WF_MAX_CONCURRENT`），速率只在上游代理里控**（每次尝试 `acquire()`）。
若要保留闸门，先统计它的放行/拒绝分布 —— 拒绝占比接近 100% 说明它是路障而非保险。

## 7. 监视器不能是被监视对象的一部分

把巡检做成「发一张卡、让 worker 去查」时，巡检本身会吃并发位、吃 RPM，并与被巡检对象抢同一份配额。
实测最坏形态：一段 30 分钟的上游故障里，**107.8 RPM 的风暴源正是巡检 worker**，而同段巡检卡
被派了 3 次、全部在跑、什么都没发现 —— 它无法观测自己制造的伤害。

规则：巡检默认走**脚本 + cron，不调 LLM**；只有「必须就地改代码」的自愈才发卡，且必须幂等、
低优先级、与业务链分槽位。

## 8. 报告形态（用户要的是因果，不是过程）

汇报这类事故按「时间 → 动作 → 依据 → 真实后果」四列表给，每格都带数字；
末尾单独列「诊断错误」小节，把那些**写了但从未生效**的补丁点出来（例：模型改写只覆盖
`/v1/messages`，而实际流量是 `/v1/chat/completions` → 全日志命中 0 次）。
最后必须分清两句话：**「成功率回到 92%」不等于「吞吐恢复」**，两者要分别给数。
