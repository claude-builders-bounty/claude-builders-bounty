# changelog-gen 🚀

> 一行指令，自動產生結構化 CHANGELOG.md

## 安裝

```bash
# 下載腳本放到專案中
curl -O https://raw.githubusercontent.com/YOUR_USER/changelog-gen/main/changelog-gen.sh
chmod +x changelog-gen.sh
```

## 使用

```bash
# 從最新 tag 到 HEAD
bash changelog-gen.sh

# 從指定 tag 開始
bash changelog-gen.sh v1.0.0

# 兩個版本之間
bash changelog-gen.sh v1.0.0 v2.0.0

# 初始專案（無 tag）
bash changelog-gen.sh --init
```

## 輸出範例

```markdown
# Changelog

## [v1.2.0] - 2026-07-05

### Added
- 新增用戶註冊功能 (a1b2c3d)
- 新增即時通知模組 (e4f5g6h)

### Fixed
- 修復登入頁面崩潰問題 (i7j8k9l)

### Changed
- 升級資料庫連線池設定 (m0n1o2p)

## 分類規則

| Prefix | 分類 |
|--------|------|
| `feat:` / `add:` | Added |
| `fix:` | Fixed |
| `break:` / `refactor:` / `change:` | Changed |
| `remove:` / `delete:` | Removed |
| `doc:` | Documentation |
| `test:` | Testing |

## 授權

MIT
