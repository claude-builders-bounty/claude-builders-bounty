# Changelog

## Unreleased

### Added

- feat: 日报加认知状态行 — 服务在线/MCP数/经验沉淀条数, cron汇报可见引擎认知进展
- feat: 认知模块 cognition.py — 工具清单感知+经验沉淀, 解决引擎三大局限
- feat: 业务健康自检 health.py — 引擎自主发现结果问题(零成交天数/转化率/擦亮频率), 注入决策prompt+日报+canonical套件
- feat: autonomy模式层自主 — prompt升级(新通道/新工具/新流程提议) + 预检门槛¥2.5→¥1 + 移除不存在的--max-turns参数; 真实执行验证: 闲鱼竞争调研(¥0.145, 报告已存档LOOP/research)
- feat: 第二通道外发 — GitHub bounty 同步进任务池(19个) + gh真实评论提案(验证: warpspeed#5 comment 5236194633) + scan注入GITHUB_TOKEN + run_script支持env + P004上架(闲鱼7商品)
- feat: 商品自理闭环 — 感知真实在售(read-only/products真源) + catalog状态自动同步 + launch动作(免重复上架) + 决策prompt商品信号
- feat: 决策留痕 decisions.jsonl + 日报含Agent决策理由/实际产出清单 (修复'看不到行动')

### Fixed

- fix: learning_block 跨行条目拼接 — 经验注入丢失→结果摘要行(ad-hoc验证抓到)
- fix: audit usage匹配逻辑 — 文件数>=记账数(调试文件不算告警), 缺失才是错误
- fix: 寿命双口径(真实API消耗123天 vs 账本模拟7.6天) — 修LLM被假寿命吓到保守; audit容差校准; status_panel文案
- fix: dry-run 不再扣 LLM决策/自我审查费 (与skill文档'演练不扣费'一致)
- fix: llm_decide 超时90→150s + 失败原因落日志; 平台余额同步直连修复(防代理劫持)

### Changed

- fix+docs: 经验沉淀单行折叠(多行结果注入不丢) + 自检清理连带结果行 + README v5.3 + 首条真实经验沉淀
- docs: verify round-3 留档 12/12 PASS
- docs: final ad-hoc 验证留档 12/12 PASS
- docs: ad-hoc 验证留档 — 业务健康自检 16/16 PASS
- docs: 清理验证留档 5/5 PASS
- chore: 清理mock测试假动作(3条) — 动作流水恢复真实
- docs: HEAD verify 留档 12/12 PASS
- docs: HEAD fresh 验证留档 11/11 PASS
- chore: 运行时数据(14:00轮次+autonomy测试记账)
- docs: ad-hoc 验证留档 — autonomy模式层自主 13/13 PASS
- docs: ad-hoc 验证留档 — GitHub外发链路 14/14 PASS
- docs: ad-hoc 验证留档 — GitHub外发链路 14项
- test: canonical 验证套件 tests/verify_engine.py (商品闭环/决策/降级/记忆/寿命/审计 18项)
- docs: HEAD fresh 验证留档 — 商品自理闭环 14/14 PASS
- docs: HEAD状态 fresh 验证留档 12/12 PASS
- docs: 验证留档 — audit/双口径/prompt 9/9 PASS
- docs: 验证留档 — 寿命双口径 8/8 PASS; status_panel文案
- docs: 验证留档修正 — 12项全PASS (含回归)
- docs: 验证留档 git 固化 — 决策留痕/日报可见性 10/10 PASS
- docs: 验证留档 — dry-run扣费修复 ad-hoc 6/6 PASS
- docs: README 四层升级章节 + 验证记录
- feat(P4): report.py 引擎日报 + 主循环接入 + cron 7916c6835115 汇报升级
- feat(P1-P3): 轻量记忆注入 + fallback/expected契约 + 自我审查轮 + bump失败降级 + autonomy白名单闸门 + autonomy失败免费降级
- feat(P0.5): audit.py 常驻对账 + 修账本精度漂移 + 修 daily_burn 写死估算bug + 修 actions.jsonl 脏行
- chore: baseline snapshot before 4-layer upgrade

