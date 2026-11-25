# 项目规则说明

## 项目概述
- **项目名称**：[在此填写项目名称]
- **项目类型**：[Web应用 / 桌面应用 / CLI工具 / 库 / 其他]
- **技术栈**：[语言、框架、数据库、部署方式等]
- **创建日期**：2026-10-31

## 目录结构约定
```
xiangmu_xxx/
├── yuan_daima/          # 源代码（按模块/功能组织）
├── chengpin_shuchu/     # 构建产物、发布包、Docker镜像等
└── xiangmu_guize_shuoming.md  # 本文件
```

## 开发规范

### 代码风格
- [ ] 使用统一的代码格式化工具
- [ ] 命名规范：[camelCase / snake_case / PascalCase]
- [ ] 注释规范：[公共API必须有文档注释 / 复杂逻辑需行内注释]

### Git 工作流
- **主分支**：`main` / `master`（受保护，只能 PR 合并）
- **开发分支**：`dev` / `develop`
- **功能分支**：`feat/xxx`、`fix/xxx`、`refactor/xxx`
- **提交规范**：`type(scope): subject` (Conventional Commits)

### 测试要求
- [ ] 单元测试覆盖率 ≥ [80%]
- [ ] 新功能必须包含测试
- [ ] CI 必须通过才能合并

## 构建与部署
- **构建命令**：`[npm run build / cargo build --release / go build / python -m build]`
- **测试命令**：`[npm test / cargo test / go test ./... / pytest]`
- **部署方式**：[Docker / Vercel / AWS / 手动部署 / 其他]

## 环境变量
| 变量名 | 说明 | 必填 | 默认值 |
|--------|------|------|--------|
| `ENV_VAR_1` | 说明 | 是/否 | 值 |

## 依赖管理
- **包管理器**：[npm / pip / cargo / go mod / poetry / pnpm]
- **锁文件**：必须提交 `package-lock.json` / `Cargo.lock` / `go.sum` 等

## 重要提醒
1. **不要提交敏感信息**（API Key、密码、私钥）到仓库
2. **大文件**使用 Git LFS 或外部存储
3. **定期更新依赖**，关注安全漏洞

---
*此文件由工作区初始化脚本自动生成，请根据实际项目情况修改完善。*