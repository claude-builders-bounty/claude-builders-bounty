# Weekly GitHub Dev Summary — n8n + Claude Sonnet 4

This submission provides multiple implementations of the weekly GitHub development summary, including an exact-spec Anthropic implementation, a provider-flexible OpenRouter implementation, and a production-hardened Bulletproof Edition.

## Implementations

### 1. Exact-Spec Anthropic Reference

`04-reference-direct-anthropic.json`

This version is provided to match the bounty specification as closely as possible.

It uses n8n's native **Anthropic Chat Model** configured with:

`claude-sonnet-4-20250514`

Features:

- Friday 5 PM schedule
- GitHub commits
- Closed issues
- Merged pull requests
- AI Agent
- Native Anthropic Chat Model
- Exact requested Claude Sonnet 4 model ID
- EN/FR reporting
- Discord delivery

The workflow contains no Anthropic API key. After import, the operator must configure their own Anthropic credential in n8n.

The workflow architecture and reporting logic are based on the successfully tested OpenRouter implementation. 

## 2. OpenRouter Reference

`01-reference-openrouter.json`

This is the implementation used for the live end-to-end test.

It uses n8n's native **OpenRouter Chat Model** with:

`anthropic/claude-sonnet-4`

The OpenRouter implementation was chosen initially to keep the AI layer provider-flexible while retaining Claude Sonnet 4 for report generation.

Features:

- Friday 5 PM schedule
- GitHub commits
- Closed issues
- Merged pull requests
- AI Agent
- Claude Sonnet 4 through OpenRouter
- EN/FR reporting
- Discord delivery
- Real n8n execution test

The included execution evidence demonstrates the workflow operating end-to-end on a real n8n instance.

## 3. Bulletproof Edition

`02-bulletproof-main.json`

This version demonstrates how the same automation can be hardened for production use.

It adds:

- Preflight configuration validation
- GitHub response contract validation
- AI output validation
- External-call retries
- Configurable success-report delivery
- Explicit failure rather than silently accepting malformed data

Set `enableSuccessDelivery` in the Configuration node to `false` if the report should be generated and validated without posting to Discord.

## 4. Optional Error Handler

`03-optional-error-handler.json`

This is an optional n8n Error Trigger workflow.

When enabled and assigned as the main workflow's Error Workflow, it can:

- Receive failed workflow executions
- Identify the workflow and execution
- Capture the last executed node
- Capture the error message
- Send a Discord failure notification
- Retry the notification if Discord temporarily fails

Set `enableErrorNotifications` to `false`, or simply do not assign the Error Workflow, to disable alerts.

## Why Include Both Anthropic and OpenRouter?

The bounty specifically requests Claude Sonnet 4 using:

`claude-sonnet-4-20250514`

For exact specification alignment, `04-reference-direct-anthropic.json` uses n8n's native Anthropic Chat Model with that model ID.

The OpenRouter version is included as a provider-flexible alternative and as the implementation used for the successful live end-to-end test.

Separating the implementations keeps the bounty-compliant reference simple while also demonstrating how the AI provider can be decoupled from the workflow's GitHub collection, reporting, and delivery logic.

## Setup

### Direct Anthropic version

1. Import `04-reference-direct-anthropic.json`.
2. Configure a GitHub credential.
3. Configure an Anthropic API credential.
4. Configure the Discord webhook.
5. Set the desired repository and language.
6. Execute manually for testing.
7. Activate the workflow.

### OpenRouter version

1. Import `01-reference-openrouter.json`.
2. Configure a GitHub credential.
3. Configure an OpenRouter credential.
4. Configure the Discord webhook.
5. Set the desired repository and language.
6. Execute manually for testing.
7. Activate the workflow.

### Bulletproof Edition

Import `02-bulletproof-main.json`.

If operational failure notifications are desired, also import `03-optional-error-handler.json` and select it in the main workflow's:

**Settings → Error Workflow**

## Security

The submitted workflow files intentionally contain no live API keys, GitHub tokens, or usable Discord webhook URLs.

Never commit:

- GitHub tokens
- Anthropic API keys
- OpenRouter API keys
- Discord webhook URLs
- Other reusable secrets

## Reliability

Retries solve transient service failures. They do not solve malformed data, missing configuration, invalid AI output, or silent operational failures.

The Bulletproof Edition therefore separates:

- Retryable provider failures
- Contract and validation failures
- Operator notification

This distinction is the primary difference between a workflow that can run and one that can be operated reliably.
