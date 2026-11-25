# 飞书机器人回调服务器 - 启动指南

## 1. 安装依赖
```bash
cd D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\feishu-bot-callback
pip install -r requirements.txt
```

## 2. 配置环境变量（或直接改 main.py 里的默认值）
```bash
# Windows PowerShell
$env:FEISHU_VERIFICATION_TOKEN = "飞书控制台生成的验证Token"
$env:FEISHU_ENCRYPT_KEY = "飞书控制台生成的加密Key(Base64)"
$env:FEISHU_APP_ID = "cli_a925f05ba0b8dcd1"
```

## 3. 启动服务
```bash
python main.py
```
服务跑在 `http://localhost:8000`，回调地址：`http://localhost:8000/feishu/callback`

## 4. 用 ngrok 暴露到公网
```bash
# 安装 ngrok (若未装)
# https://ngrok.com/download

ngrok http 8000
```
得到类似 `https://abc123.ngrok-free.app` 的公网 HTTPS 地址

## 5. 飞书控制台填入
- **事件订阅** → **请求地址**：`https://abc123.ngrok-free.app/feishu/callback`
- **验证 Token** & **加密 Key**：填第 2 步设置的值
- 勾选事件：`im.message.receive_v1`（接收消息）
- **权限管理** → 申请 `im:message:read` `im:message:receive` `mention:read` 等
- **版本发布** → 创建版本 → 发布上线

## 6. 测试
在群里 @机器人 发句话，控制台会打印收到的消息，机器人会原样回复"收到: xxx"

## 注意
- ngrok 免费版每次重启地址变，需同步更新控制台
- 生产环境请用固定域名 + HTTPS
- tenant_access_token 需定时刷新（main.py 里预留了 `set_cached_token` 接口）