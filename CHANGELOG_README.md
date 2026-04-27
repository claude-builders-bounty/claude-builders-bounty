# CHANGELOG 生成器

用git历史自动生成结构化CHANGELOG.md。

## 安装

```bash
# 复制脚本到项目根目录
cp changelog.sh /your-project/
chmod +x changelog.sh
```

## 用法

```bash
# 从上一个tag到HEAD（默认）
./changelog.sh

# 指定输出文件和范围
./changelog.sh CHANGELOG.md v1.0.0..HEAD

# 所有提交（包括初始）
./changelog.sh CHANGELOG.md $(git rev-list --max-parents=0 HEAD)..HEAD
```

## 分类规则

| 提交前缀 | 分类 |
|---------|------|
| feat/add/new/implement/create | Added |
| fix/bug/patch/hotfix | Fixed |
| change/update/refactor/improve | Changed |
| remove/deprecate/delete | Removed |
| docs/readme | Documentation |
| 其他 | Other |

## 输出示例

```markdown
# Changelog

> 自动从git历史生成 | 范围: v0.1.0..HEAD

## Added

- **添加用户登录功能** (abc1234) — Alice

## Fixed

- **修复空指针异常** (def5678) — Bob
```

3个步骤即可使用：
1. 复制脚本到项目
2. `chmod +x changelog.sh`
3. `./changelog.sh`
