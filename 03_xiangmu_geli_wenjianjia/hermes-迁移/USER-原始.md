User: completely autonomous execution, 10-min reports (only money earned), legal only (no gray market), prefers domestic payout (WeChat/Alipay) but accepts USDC→exchange→WeChat/Alipay, verification-first (must verify commands/APIs/platforms before executing), direct Chinese communication, no AI fluff, rejects AI content generation, only automation. Wallet: 0x2e13ADd5A2b92B2650CB3D40d13eD9D83305ED76 (private key in ~/.hermes/wallet/wallet.json, P-256 key in ~/.hermes/wallet/p256_key.json). Strategy: normal pricing (75-80% budget) + extreme delivery quality → 5-star reviews → reputation score flies → exponential win rate. Env: Windows + WSL2 Ubuntu 24.04, Hermes Agent + Nemotron 3 Ultra + local qwen2.5-vl:7b. Active platforms: dealwork.ai (14 tasks/轮, USD+Stripe, 主力), HYRVE (Agent在线, 心跳正常), ClawMart (5任务提交, 缺CNY支付网关), 波街 (前台实时在线, daemon前台运行), UUMit/minia2a/others (长尾). dealwork.ai claim URL: https://dealwork.ai/dashboard/agents/claim/4b0325dc-5798-4a62-8d9c-d58b695bdee7 (registered but not claimed). Work style: completely autonomous, 10-min reports (only money earned), verification-first, direct Chinese, no AI fluff, legal only. Strategy: normal pricing (75-80% budget) + extreme delivery quality → 5-star reviews → reputation score flies → exponential win rate. 10-min reports only money earned.
§
隐私取向：对外暴露面的东西一律要私有 —— 建群被要求从 public 改成 private「防止其他人进来」。凡涉及共享资源（群组、分享链接、对外服务）默认取最严私有设置，需要公开时必须先问。
§
委派预期：用户给的是**整体授权**，清单/步骤只是执行细节。把宽泛任务收窄成一份「必查清单」去执行，会被当场纠正——他要的是覆盖整体，不是把清单打钩交差。任何任务卡/子任务/定时任务说明都必须：主任务写完整范围并占据主体，已知项清单显式标注为「起点，不是范围上限」，并写明禁止「只做完清单上的 N 条就交差」。
§
自动化流水线的处置偏好（2026-10-18 明确要求）：不接受「挂起等人工」。任何卡/任务卡住时，要么自动重试，要么直接打回重做——不允许既不过也不打回地停在中间状态，那等于流水线死掉。同时必须防死循环：打回时必须写清具体原因和改法让执行方照着改，且要有上限（反复不过就归档退出循环），不能无限重打把资源耗光。
§
User's core need: Simple architecture — code tasks → Claude Code, non-code tasks → Hermes (in-session), Hermes reviews/verifies code. Rejects complex multi-agent frameworks (kanban-agency, hermes-conductor, etc.) as over-engineering. Prefers direct use of existing assets: xiangmu kanban, hermes-wf scripts, claude -p headless.
§
权限/环境类问题：要求「一次性全量配齐，能给的都给」，不接受逐个踩坑再补。发现一类权限/配置缺口时，主动把同类 agent/组件全量审计并一次修完（含自动预检与救护脚本），只修当前报错那一个会被追问。
§
User work style: completely autonomous execution; 10-min reports (only money earned); legal only (no gray market); prefers domestic payout (WeChat/Alipay) but accepts USDC→exchange→WeChat/Alipay; verification-first (must verify commands/APIs/platforms before executing); direct Chinese communication, no AI fluff; rejects AI content generation, only automation. Core instruction: "把所有的agent的环境，环境变量，该配置的，改给的权限，能给的都给一下。别再出这问题了" — full environment setup upfront, not incremental.
§
Process requirements: "别忘了看板" — must monitor kanban board; "你干嘛呢？不是走Claude code？" — code tasks MUST go through Claude Code workflow; "杀掉当前下载，换镜像重来" — decisive about fixing download issues; "不接受挂起等人工" — any stuck card must auto-retry or bounce back with clear fix instructions, not wait for human; task cards must cover full scope, not just checklist items ("清单是起点，不是范围上限").
§
Privacy: shared resources (groups, share links, public services) default to most restrictive private settings; must ask before making anything public.
§
Core instruction: "把所有的agent的环境，环境变量，该配置的，改给的权限，能给的都给一下。别再出这问题了" — full environment setup upfront, not incremental. All code tasks MUST go through Kanban → Claude Code (cc-*) workflow; coordinator must NOT write code/fix bugs directly.
§
Work style: completely autonomous execution; 10-min reports (only money earned); legal only; prefers domestic payout (WeChat/Alipay); verification-first (must verify commands/APIs/platforms before executing); direct Chinese communication, no AI fluff; rejects AI content generation, only automation.
§
Process: "别忘了看板" — must monitor kanban board; "不接受挂起等人工" — stuck cards must auto-retry or bounce back with clear fix instructions, not wait for human; task cards must cover full scope, not just checklist items ("清单是起点，不是范围上限").
§
test