"""
飞书机器人回调服务器 - 最小可用版
配合 ngrok 使用: ngrok http 8000
"""
import os
import json
import logging
from typing import Dict, Any
from fastapi import FastAPI, Request, Header, HTTPException
from fastapi.responses import JSONResponse
import uvicorn
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
import base64

# ===== 配置区（填你的）=====
VERIFICATION_TOKEN = os.getenv("FEISHU_VERIFICATION_TOKEN", "你的验证Token")
ENCRYPT_KEY = os.getenv("FEISHU_ENCRYPT_KEY", "你的加密Key")  # Base64 编码的 32 字节
APP_ID = os.getenv("FEISHU_APP_ID", "cli_a925f05ba0b8dcd1")
# ===========================

app = FastAPI(title="Feishu Bot Callback")
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ----- AES-256-CBC 解密（飞书加密回调用）-----
def decrypt_aes256_cbc(encrypted_b64: str, key_b64: str) -> str:
    key = base64.b64decode(key_b64)
    data = base64.b64decode(encrypted_b64)
    iv = data[:16]
    ciphertext = data[16:]
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv))
    decryptor = cipher.decryptor()
    padded = decryptor.update(ciphertext) + decryptor.finalize()
    unpadder = padding.PKCS7(128).unpadder()
    return (unpadder.update(padded) + unpadder.finalize()).decode("utf-8")

# ----- URL 验证挑战（事件订阅开启时飞书会调一次）-----
@app.post("/feishu/callback")
async def feishu_callback(
    request: Request,
    x_feishu_signature: str = Header(None),
    x_feishu_timestamp: str = Header(None),
    x_feishu_nonce: str = Header(None),
):
    body_bytes = await request.body()
    body_str = body_bytes.decode("utf-8")
    logger.info(f"收到回调: {body_str[:500]}")

    try:
        payload = json.loads(body_str)
    except json.JSONDecodeError:
        raise HTTPException(400, "Invalid JSON")

    # 1. URL 验证挑战
    if payload.get("type") == "url_verification":
        challenge = payload.get("challenge", "")
        logger.info(f"URL 验证挑战: {challenge}")
        return JSONResponse({"challenge": challenge})

    # 2. 加密回调解密
    if "encrypt" in payload:
        if not ENCRYPT_KEY or ENCRYPT_KEY == "你的加密Key":
            raise HTTPException(500, "ENCRYPT_KEY 未配置")
        decrypted = decrypt_aes256_cbc(payload["encrypt"], ENCRYPT_KEY)
        payload = json.loads(decrypted)
        logger.info(f"解密后: {json.dumps(payload, ensure_ascii=False)[:500]}")

    # 3. 验证 Token
    if payload.get("token") != VERIFICATION_TOKEN:
        logger.warning(f"Token 校验失败: 期望={VERIFICATION_TOKEN}, 实际={payload.get('token')}")
        raise HTTPException(403, "Invalid verification token")

    # 4. 处理事件
    event_type = payload.get("header", {}).get("event_type")
    event = payload.get("event", {})

    if event_type == "im.message.receive_v1":
        await handle_message(event)

    return JSONResponse({"status": "ok"})


async def handle_message(event: Dict[str, Any]):
    """处理接收到的消息"""
    message = event.get("message", {})
    msg_type = message.get("message_type")
    content = message.get("content", "{}")
    chat_id = message.get("chat_id")
    open_id = event.get("sender", {}).get("sender_id", {}).get("open_id")

    logger.info(f"收到消息: type={msg_type}, chat_id={chat_id}, open_id={open_id}, content={content}")

    # 只演示：收到文本消息 -> 原样回复
    if msg_type == "text":
        try:
            text = json.loads(content).get("text", "")
            if text:
                await reply_text(chat_id, f"收到: {text}")
        except Exception as e:
            logger.error(f"处理文本消息失败: {e}")


async def reply_text(chat_id: str, text: str):
    """调用飞书 API 回复文本消息"""
    import httpx

    # 这里需要 tenant_access_token，实际用时要缓存并定时刷新
    # 简化演示：直接用全局变量（生产环境请用 Redis/内存缓存 + 定时刷新）
    token = getattr(reply_text, "cached_token", None)
    if not token:
        logger.warning("tenant_access_token 未缓存，无法回复")
        return

    url = "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=chat_id"
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    data = {"receive_id": chat_id, "msg_type": "text", "content": json.dumps({"text": text})}

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.post(url, headers=headers, json=data)
            logger.info(f"回复结果: {resp.status_code} {resp.text}")
    except Exception as e:
        logger.error(f"发送回复失败: {e}")


def set_cached_token(token: str):
    """外部调用刷新 token 时用"""
    reply_text.cached_token = token
    logger.info("tenant_access_token 已更新")


# ----- 健康检查 -----
@app.get("/health")
async def health():
    return {"status": "ok", "app_id": APP_ID}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)