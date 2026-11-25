# Cookie 字段详解

## 必需 Cookie 字段（从 goofish.com 获取）

| 字段名 | 说明 | 示例 | 必需性 |
|--------|------|------|--------|
| `_m_h5_tk` | MTOP 签名 token，格式：`token_timestamp` | `0c0e9d15c716fd4a925ff58b0218b035_1791784601636` | ✅ 必须 |
| `_m_h5_tk_enc` | 加密 token，用于签名验证 | `9f81fbfe5e24c43ef5552dd5d2609639` | ✅ 必须 |
| `cookie2` | 二代 cookie，标识用户会话 | `11fdc1299f91162143034adf4a82375d` | ✅ 必须 |
| `t` | 时间戳 | `6aa5f063db55831ed8f67a31b76f4826` | ✅ 必须 |
| `cna` | 设备指纹，阿里巴巴跨域追踪 | `B9UWI1QwrggCAWUW1qNhBYMm` | ✅ 必须 |
| `xlly_s` | 登录态标识 | `1` | ✅ 必须 |
| `_tb_token_` | 淘宝 token | `e4d36f49eeb46` | ✅ 必须 |
| `_samesite_flag_` | SameSite 标志 | `true` | 推荐 |
| `sgcookie` | 安全 cookie，含加密信息 | `E100UXQJa%2FiaBc6XT4kUgg...` | 推荐 |
| `tracknick` | 追踪昵称（URL 编码） | `%E7%99%BB%E5%BD%95%E5%90%8D34819770` | 推荐 |
| `unb` | 用户数字 ID | `3478508742` | 推荐 |
| `havana_lgc2_77` | 登录态加密载荷 | `eyJoaW...USJ9` | 推荐 |
| `tfstk` | 安全 token，长字符串 | `gE2qdvvUltBqeFQ3YkDN4fXwaglx3A7C_...` | 可选 |

## 获取方法
1. 浏览器打开 https://www.goofish.com 并登录
2. F12 打开开发者工具
3. Application 标签 -> Cookies -> https://www.goofish.com
3. 复制所有 Cookie，格式化为 `k=v; k=v; ...`

## Cookie 有效期
- `_m_h5_tk` / `_m_h5_tk_enc`：通常 2 小时过期，需定时刷新
- `cookie2` / `cna` / `xlly_s`：长期有效（月级别）
- 建议每 1 小时检查一次 `_m_h5_tk` 是否过期，过期则重新登录获取

## 常见问题
| 现象 | 原因 | 解决 |
|------|------|------|
| 登录态失效 | `_m_h5_tk` 过期 | 重新登录浏览器，重新获取 Cookie |
| 签名验证失败 | `_m_h5_tk_enc` 不匹配 | 确保 `_m_h5_tk` 和 `_m_h5_tk_enc` 成对获取 |
| 设备指纹异常 | `cna` / `xlly_s` 缺失 | 完整复制所有 Cookie 字段 |
| 频繁验证码 | 同 IP 多账号 / 频率过高 | 降低频率、一机一号一 IP |