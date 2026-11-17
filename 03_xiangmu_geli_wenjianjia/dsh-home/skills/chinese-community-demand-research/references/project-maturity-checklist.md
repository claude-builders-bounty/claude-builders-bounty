# GitHub Project Maturity Checklist — 15-Point Evaluation Rubric

## Scoring: Each criterion 0-2 points. Total 30. Tiers: 25+ ★★★★★ | 20-24 ★★★★☆ | 15-19 ★★★☆☆ | 10-14 ★★☆☆☆ | <10 ★☆☆☆☆

---

## 1. Documentation & Onboarding (0-2 each)

| Criterion | 0 | 1 | 2 |
|-----------|---|---|---|
| **README Language** | English only | Mixed/Partial Chinese | Full Chinese + English |
| **Install Guide** | None / "figure it out" | Basic steps, manual config | One-liner: Docker/Release/Action/Script |
| **Usage Examples** | None | Minimal CLI flags | Rich examples: common workflows, screenshots |
| **Architecture Docs** | None | High-level only | Component diagram, data flow, extension points |

---

## 2. Release & Distribution (0-2 each)

| Criterion | 0 | 1 | 2 |
|-----------|---|---|---|
| **Release Artifacts** | Source only | Binaries for 1 platform | Multi-platform binaries + Docker + package managers |
| **Versioning** | No tags / random | Irregular tags | SemVer, changelog, GitHub Releases |
| **Auto-Update** | None | Manual check | Built-in check / winget / scoop / brew / apt |

---

## 3. Code Health & Activity (0-2 each)

| Criterion | 0 | 1 | 2 |
|-----------|---|---|---|
| **Commit Recency** | >1 year | 1-6 months | <1 month |
| **Issue Hygiene** | 100+ open, no response | Some triage, slow response | Active triage, labels, <7 day first response |
| **PR Handling** | Ignored / no CI | Basic CI, slow merge | CI + review + auto-merge for deps |
| **Test Coverage** | None | Unit only | Unit + integration + e2e |

---

## 4. Usability & Deployment Friction (0-2 each)

| Criterion | 0 | 1 | 2 |
|-----------|---|---|---|
| **Config Complexity** | Edit 5+ files, env vars | 1 config file + env | Zero-config / GUI / wizard / auto-detect |
| **Dependency Hell** | Manual pip/npm + system deps | Docker but manual build | Official Docker Hub / prebuilt binary |
| **Cross-Platform** | Linux only | Linux + macOS | Win / Mac / Linux / ARM / Android |
| **Resource Footprint** | Heavy (GBs RAM, no limits) | Moderate | Light, configurable limits |

---

## 5. Community & Ecosystem (0-2 each)

| Criterion | 0 | 1 | 2 |
|-----------|---|---|---|
| **Third-Party Tutorials** | None | 1-2 blog posts | 多平台教程: 少数派/知乎/CSDN/B站/YouTube |
| **Plugin/Extension System** | None | Basic hooks | Rich plugin API, marketplace, docs |
| **Commercial Friendly License** | GPL/AGPL/Non-commercial | LGPL/MPL | MIT/Apache-2.0/BSD |
| **Bus Factor** | 1 maintainer, no deputies | 2-3 active | 3+ or org-owned, governance doc |

---

## 6. Problem-Solution Fit (0-2 each)

| Criterion | 0 | 1 | 2 |
|-----------|---|---|---|
| **Solves Core Pain** | Partial / workaround | Core features work | Complete + edge cases handled |
| **Performance** | Slow / crashes on scale | Acceptable | Optimized, benchmarks published |
| **Error Handling** | Cryptic / crashes | Basic messages | User-friendly, actionable, i18n |
| **Security Posture** | No audit, secrets in code | Basic hygiene | Supply chain, SBOM, dependabot |

---

## Quick Triage Decision Matrix

| Score | Action |
|-------|--------|
| **25-30** | **Promote directly** — wrap with GUI/installer, write Chinese tutorial, submit to 少数派/酷安/GitHub Trending |
| **20-24** | **Wrap & polish** — add Dockerfile, GitHub Action, Chinese README, config UI, auto-update |
| **15-19** | **Fork & fix** — identify 2-3 blockers, PR upstream, maintain friendly fork |
| **10-14** | **Reference only** — study architecture, rewrite critical path, or find alternative |
| **<10** | **Avoid** — dead end, high maintenance burden |

---

## Red Flags (Auto-Disqualify or Heavy Penalty)

- [ ] **No commits in 12+ months** + open security issues
- [ ] **License changes** to restrictive (BSL, SSPL, custom "no commercial")
- [ ] **Author hostile** to contributions / ignores PRs / closes issues without reason
- [ ] **Hardcoded secrets** / API keys in repo history
- [ ] **Malware flags** / suspicious obfuscation / unauthorized data collection
- [ ] **Legal gray zone** without clear disclaimer (DRM removal, paid API scraping, ToS violation)
- [ ] **Architecture mismatch** — e.g., Electron app for headless server task, Python CLI for non-tech users
- [ ] **Government/Judicial/Regulatory data source** — court docs, bidding, drug reg, patents, customs (criminal liability risk)
- [ ] **Private API scraping** — WeChat/Douyin/Xianyu non-official APIs (ToS violation, account bans)
- [ ] **DRM/Copyright circumvention** — encrypted video, game assets, paid content bypass
- [ ] **PII/Personal data without consent** — chat logs, profiles, location (PIPL/CSL/GDPR violation)

## Individual-Executable Criteria (User Requirement: "落地难，找适合个人的")

A project is **individually executable** ONLY when ALL pass:

| Criterion | Pass | Fail |
|-----------|------|------|
| **Team Dependency** | Single person builds/deploys/operates/supports | Requires co-founders, employees, contractors |
| **Sales Cycle** | Platform-native (Mini Program/Chrome Store/Gumroad/闲鱼/MS Store) | Enterprise B2B, procurement, legal review |
| **Cash Flow** | T+1 to T+7 (platform direct payout) | Net-30/60/90, invoicing, collections |
| **Maintenance** | < 10 hrs/week (automated ops, self-serve) | > 20 hrs/week, high-touch support, manual ops |
| **Startup Cost** | < ¥5,000 (dev tools only, no inventory/ads) | > ¥20,000 (inventory, paid ads, compliance, legal) |
| **Platform Risk** | Single platform dependency OK | Multi-platform required, high switching cost |
| **Regulatory** | No license/permit/filing needed | ICP/EDI/ICP备案, 行业资质, 算法备案, 安评 |

**Reject entire direction** if any criterion fails. This filters out: enterprise SaaS, marketplace platforms, hardware, regulated industries (fintech/health/edu), team-required ops.

---

## Weighting by Use Case

| Use Case | Weights |
|----------|---------|
| **End-user tool (GUI/CLI)** | Usability 40%, Docs 30%, Release 20%, Health 10% |
| **Library / SDK** | Health 35%, Docs 30%, Ecosystem 20%, Release 15% |
| **Self-hosted service** | Release 30%, Health 25%, Security 25%, Usability 20% |
| **Automation / CI tool** | Health 35%, Release 25%, Usability 20%, Docs 20% |

---

## Automation: Batch Scoring Script

```python
#!/usr/bin/env python3
# scripts/score_project.py — Run against GitHub API + local clone
# Usage: python score_project.py owner/repo

import subprocess, json, sys, re
from datetime import datetime, timedelta

def gh_api(path):
    return json.loads(subprocess.check_output(["gh", "api", path], text=True))

def score_repo(repo):
    repo_data = gh_api(f"/repos/{repo}")
    commits = gh_api(f"/repos/{repo}/commits?per_page=1")
    issues = gh_api(f"/repos/{repo}/issues?state=all&per_page=100")
    releases = gh_api(f"/repos/{repo}/releases?per_page=5")
    
    # Compute signals
    last_commit_days = (datetime.now() - datetime.fromisoformat(commits[0]['commit']['author']['date'].replace('Z', '+00:00'))).days
    open_issues = len([i for i in issues if i['state'] == 'open'])
    closed_issues = len([i for i in issues if i['state'] == 'closed'])
    issue_response_rate = closed_issues / max(1, open_issues + closed_issues)
    has_docker = any('docker' in r.get('assets', []) for r in releases)
    has_binaries = len(releases) > 0 and any(a['browser_download_url'] for r in releases for a in r['assets'])
    
    # Simplified scoring
    score = 0
    score += 2 if last_commit_days < 30 else (1 if last_commit_days < 180 else 0)
    score += 2 if issue_response_rate > 0.5 else (1 if issue_response_rate > 0.2 else 0)
    score += 2 if has_binaries else (1 if has_docker else 0)
    score += 2 if repo_data['license'] and repo_data['license']['spdx_id'] in ['MIT', 'Apache-2.0', 'BSD-3-Clause'] else 0
    score += 2 if '中文' in (repo_data.get('description') or '') or 'Chinese' in (repo_data.get('description') or '') else 0
    
    return score

if __name__ == "__main__":
    repo = sys.argv[1] if len(sys.argv) > 1 else "owner/repo"
    print(f"{repo}: {score_repo(repo)}/10 (quick)")
```

---

## Reference Projects by Tier (This Session's Data)

### ★★★★★ (25+) — Promote Directly
- `kovidgoyal/calibre` — E-book management gold standard
- `Motrix/Motrix` — Download manager, cross-platform, active
- `qBittorrent/qBittorrent` — BT client, feature-complete
- `iDvel/rime-ice` — Rime config, actively maintained, one-click
- `yt-dlp/yt-dlp` — Video downloader, 1000+ sites, daily updates

### ★★★★☆ (20-24) — Wrap & Polish
- `cshuangyy/videdown` — Modern UI, Electron, needs Windows installer
- `ScottSloan/Bili23-Downloader` — B站专用, 高画质, 需自动更新
- `erikzhuang55/Bilitato` — Browser extension, AI features, 发布流程需完善
- `NanmiCoder/MediaCrawler` — Multi-platform crawler, 文档需中文化
- `ollama/ollama` — Local LLM, 需模型管理 GUI
- `AUTOMATIC1111/stable-diffusion-webui` — SD WebUI, 启动脚本需优化
- `LunaTranslator/LunaTranslator` — VN翻译, 需打包分发

### ★★★☆☆ (15-19) — Fork & Fix
- `chiupam/tieba` — GitHub Actions签到, 无Web面板, 多账号管理弱
- `shitianshiwa/Tieba-Cloud-Review` — 吧务脚本, 部署门槛高, 无GUI
- `nixliuxin/Tieba-Time-Machine` — 归档工具, 仅CLI, 无增量同步
- `binbyu/Reader` — 小说阅读器, epub渲染弱, 无云同步
- `jiji262/douyin-downloader` — 抖音下载, 维护频率低

### ★★☆☆☆ (10-14) — Reference Only
- `clb-128258/TiebaDesktop` — PyQt客户端, 早期, 功能不全
- `talebook/talebook` — Calibre Web, 部署复杂, 移动端弱

---

## Maintenance Notes
- Re-score quarterly or on major version bump
- Track score delta: improving = good signal, declining = fork risk
- Share scorecards with community (issue/PR) to encourage improvement