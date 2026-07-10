# CLAUDE.md — Next.js + SQLite SaaS

> 自动生成 by 雨燕车间 (AAP). Bounty: [BOUNTY $75] TEMPLATE: CLAUDE.md for a Next.js + SQLite SaaS project

## 项目概览
## 💰 Bounty: $75 — powered by [Opire](https://opire.dev)

## Description
Create an opinionated, production-ready `CLAUDE.md` for a typical SaaS project
built with Next.js 15 App Router and SQLite (better-sqlite3 or Turso).

## Acceptance Criteria
- [ ] Covers: project structure, naming conventions, DB migration rules
- [ ] Includes: dev commands, patterns to follow, anti-patterns to avoid
- [ ] Opinionated — not generic. Every rule has a reason.
- [ ] Usable without modification on a greenfield Next.js + SQLite project
- [ ] Tested: create a new project, paste the CLAUDE.md, confirm Claude Cod

## 开发命令
- `npm run dev` 启动开发服务器
- `npm run build` 生产构建
- `npm test` 跑测试

## 架构约定
- App Router (Next.js 13+)
- SQLite 经 better-sqlite3 做本地存储
- 环境变量放 .env.local (不提交)

## 给 Claude Code 的约束
- 改动先跑 lint+test 再提
- 不引入未声明的依赖
- DB schema 变更需 migration 文件
