---
name: opentask-registration
description: OpenTask.ai 自动化注册与任务接入，基于 DPoP/JWS 认证 + QQ 邮箱验证码
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [opentask, registration, dpop, jws, email-verification, revenue]
    related_skills: [payment-gateway, lead-generator]
    requires_toolsets: [terminal, web, file, web_search]
---

# OpenTask.ai 自动化注册

**核心使命**：实现 OpenTask.ai 平台的全自动化注册（DPoP/JWS 认证）、邮箱验证码自动获取、Agent 上架、任务轮询与接单。

---

## 🔐 认证流程分析

OpenTask.ai 使用 **DPoP (Demonstrating Proof of Possession) + JWS** 认证流程：

1. **挑战获取**: `POST /api/agent/auth/register/challenge` → 获取 challenge
2. **JWS 签名**: 使用 P-256 私钥签名 challenge
3. **注册完成**: `POST /api/agent/auth/register/complete` 提交签名
4. **获取 Token**: 返回 Bearer Token
5. **邮箱验证**: 可能需要邮箱验证码

---

## 🔧 核心实现

```python
import json
import base64
import hashlib
import uuid
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import Encoding, PrivateFormat, NoEncryption
import jwt
import time

class OpenTaskRegistration:
    def __init__(self, email_cookies: dict):
        self.base_url = "https://opentask.ai"
        self.email_cookies = email_cookies
        self.private_key = None
        self.public_key = None
        self.access_token = None
        self.agent_id = None
    
    def generate_p256_keypair(self):
        """生成 P-256 密钥对"""
        self.private_key = ec.generate_private_key(ec.SECP256R1())
        self.public_key = self.private_key.public_key()
        return self.private_key, self.public_key
    
    def export_keys(self) -> dict:
        """导出密钥用于持久化"""
        private_pem = self.private_key.private_bytes(
            encoding=Encoding.PEM,
            format=PrivateFormat.PKCS8,
            encryption_algorithm=NoEncryption()
        ).decode()
        public_pem = self.public_key.public_bytes(
            encoding=Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode()
        return {"private_key": private_pem, "public_key": public_pem}
    
    def load_keys(self, private_pem: str, public_pem: str):
        """加载已有密钥"""
        self.private_key = serialization.load_pem_private_key(
            private_pem.encode(), password=None
        )
        self.public_key = serialization.load_pem_public_key(
            public_pem.encode()
        )
    
    def create_jws(self, payload: dict) -> str:
        """创建 JWS 签名 (ES256)"""
        header = {
            "alg": "ES256",
            "typ": "JWT",
            "jwk": {
                "kty": "EC",
                "crv": "P-256",
                "x": self._b64url_encode(self.public_key.public_numbers().x.to_bytes(32, 'big')),
                "y": self._b64url_encode(self.public_key.public_numbers().y.to_bytes(32, 'big')),
            }
        }
        payload["iat"] = int(time.time())
        payload["jti"] = str(uuid.uuid4())
        
        token = jwt.encode(
            payload,
            self.private_key,
            algorithm="ES256",
            headers=header
        )
        return token
    
    def _b64url_encode(self, data: bytes) -> str:
        return base64.urlsafe_b64encode(data).rstrip(b'=').decode()
    
    def register(self) -> bool:
        """完整注册流程"""
        # 1. 生成/加载密钥对
        if not self.private_key:
            self.generate_p256_keypair()
        
        # 2. 获取挑战
        challenge = self.get_challenge()
        if not challenge:
            return False
        
        # 3. 签名挑战
        signed_challenge = self.sign_challenge(challenge)
        
        # 4. 完成注册
        return self.complete_registration(signed_challenge)
    
    def get_challenge(self) -> Optional[str]:
        """获取注册挑战"""
        try:
            response = self._http_post(
                "/api/agent/auth/register/challenge",
                json={"public_key": self.export_keys()["public_key"]}
            )
            return response.get("challenge")
        except Exception as e:
            log(f"[OpenTask] Get challenge failed: {e}")
            return None
    
    def sign_challenge(self, challenge: str) -> str:
        """签名挑战"""
        payload = {"challenge": challenge}
        return self.create_jws(payload)
    
    def complete_registration(self, signed_challenge: str) -> bool:
        """完成注册"""
        try:
            response = self._http_post(
                "/api/agent/auth/register/complete",
                json={"signed_challenge": signed_challenge}
            )
            self.access_token = response.get("access_token")
            self.agent_id = response.get("agent_id")
            return bool(self.access_token)
        except Exception as e:
            log(f"[OpenTask] Complete registration failed: {e}")
            return False
    
    def _http_post(self, endpoint: str, json: dict = None) -> dict:
        """发送 HTTP POST 请求"""
        import urllib.request
        import json as json_module
        
        url = f"{self.base_url}{endpoint}"
        data = json_module.dumps(json).encode() if json else None
        req = urllib.request.Request(
            url,
            data=data,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Hermes Agent",
                "Cookie": self._build_cookie_header()
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json_module.loads(resp.read().decode())
    
    def _build_cookie_header(self) -> str:
        """构建 Cookie 头"""
        return "; ".join([f"{c['name']}={c['value']}" for c in self.email_cookies])
    
    def verify_email(self) -> bool:
        """自动获取邮箱验证码并完成验证"""
        # 使用 QQ 邮箱 Cookie 访问邮箱获取验证码
        # 解析验证码链接并点击
        pass
    
    def poll_tasks(self) -> List[dict]:
        """轮询任务"""
        if not self.access_token:
            return []
        # 实现任务轮询
        pass
    
    def execute_task(self, task: dict) -> bool:
        """执行任务"""
        pass
```

---

## 📋 注册流程自动化清单

- [x] P-256 密钥对生成/加载
- [x] 获取注册挑战
- [x] JWS (ES256) 签名挑战
- [x] 完成注册获取 Token
- [ ] QQ 邮箱自动获取验证码
- [ ] 邮箱验证码自动提交
- [ ] Agent 信息完善
- [ ] 技能标签配置
- [ ] 任务轮询接入主循环

---

## 🔧 集成到主循环

```python
class OpenTaskHandler(PlatformHandler):
    def __init__(self, platform: dict):
        super().__init__(platform)
        self.registration = OpenTaskRegistration(
            email_cookies=load_qq_cookies()
        )
    
    def register(self) -> bool:
        if is_platform_registered(self.name):
            self.creds = get_platform_credentials(self.name)
            return True
        
        if self.registration.register():
            creds = {
                "agent_id": self.registration.agent_id,
                "access_token": self.registration.access_token,
                "private_key": self.registration.export_keys()["private_key"],
                "public_key": self.registration.export_keys()["public_key"],
            }
            update_platform_credentials(self.name, creds)
            self.creds = creds
            log(f"[{self.name}] Registered: {self.registration.agent_id}")
            return True
        log(f"[{self.name}] Registration failed")
        return False
    
    def poll_tasks(self) -> List[dict]:
        if not self.creds or not self.creds.get("access_token"):
            return []
        # 实现任务轮询
        return []
    
    def execute_task(self, task: dict) -> bool:
        # 实现任务执行
        return False
```

---

## 📋 部署清单

- [ ] 安装 `cryptography` `pyjwt` 依赖
- [ ] 配置 QQ 邮箱 Cookie
- [ ] 实现邮箱验证码自动获取
- [ ] 接入主循环
- [ ] 测试完整注册流程
- [ ] 接入任务轮询与执行

---

## 📋 依赖

```bash
pip install cryptography pyjwt
```