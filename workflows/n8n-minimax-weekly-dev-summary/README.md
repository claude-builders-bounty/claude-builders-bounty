# n8n + MiniMax Weekly Dev Summary

Automated weekly developer summary using n8n, GitHub API, and MiniMax Text-01.

## Setup (5 Steps)

**1. Import Workflow**
- n8n → Settings → Import from File → select `weekly-dev-summary.json`

**2. Configure Credentials**
- GitHub PAT: Settings → Variables → `GITHUB_TOKEN`
- MiniMax API Key: Settings → Variables → `MINIMAX_CN_API_KEY`
- SMTP Password: Settings → Credentials → Outlook (mm1556@msn.com / mm010506)

**3. Set Variables**
| Variable | Value |
|----------|-------|
| `github_repo` | Your target repo (e.g. `owner/repo`) |
| `email_from` | mm1556@msn.com |
| `email_to` | mm1556@msn.com |
| `language` | ZH |

**4. Configure GitHub PAT**
- Token needs: `repo`, `read:user`, `read:org`
- Settings → Developer settings → Personal access tokens → Generate new token

**5. Test Run**
- Click "Test workflow" in n8n
- Check email for summary output

## Workflow Flow
1. **Cron** (Friday 5pm `0 17 * * 5`)
2. **Date Helper** (calculates 7 days ago)
3. **GitHub API** (fetches commits + issues + PRs)
4. **Merge** (combines data)
5. **MiniMax Text-01** (generates Chinese summary)
6. **Translate** (ensures Chinese output)
7. **Email** (sends to mm1556@msn.com via Outlook SMTP)
