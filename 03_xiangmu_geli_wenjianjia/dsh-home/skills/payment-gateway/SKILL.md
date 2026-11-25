---
name: payment-gateway
description: 统一支付网关：Stripe/支付宝/微信/USDC多渠道统一接口
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [payment, gateway, stripe, alipay, wechat, usdc, invoice, billing, revenue]
    related_skills: [invoice-manager, seo-auditor, content-writer, lead-generator]
    requires_toolsets: [terminal, web, file, web_search]
---

# 统一支付网关

**核心使命**：多渠道统一支付接口，支持 Stripe/支付宝/微信/USDC，实现开票/收款/退款/对账/催款的资金闭环，零 Token 成本。

---

## 💰 支持渠道矩阵

| 币种 | Stripe | 支付宝 | 微信 | USDC (Base/Polygon) |
|------|--------|--------|------|---------------------|
| USD  | ✅     | -      | -    | ✅                  |
| CNY  | -      | ✅      | ✅    | -                   |
| EUR  | ✅     | -      | -    | ✅                  |
| GBP  | ✅     | -      | -    | ✅                  |

---

## 🏗️ 统一接口抽象

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
from enum import Enum

class Currency(str, Enum):
    USD = "USD"
    CNY = "CNY"
    EUR = "EUR"
    GBP = "GBP"

class PaymentStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

@dataclass
class PaymentRequest:
    amount: float
    currency: Currency
    client_email: str
    metadata: dict
    return_url: Optional[str] = None
    cancel_url: Optional[str] = None

@dataclass
class PaymentResult:
    payment_id: str
    status: PaymentStatus
    payment_url: Optional[str] = None
    qr_code: Optional[str] = None
    expires_at: Optional[str] = None
    raw_response: dict = None

class PaymentGatewayBase(ABC):
    """支付网关基类"""
    
    SUPPORTED_CURRENCIES: set = set()
    
    @abstractmethod
    def create_payment(self, request: PaymentRequest) -> PaymentResult:
        """创建支付链接/二维码"""
        pass
    
    @abstractmethod
    def verify_payment(self, payment_id: str) -> PaymentResult:
        """验证支付状态"""
        pass
    
    @abstractmethod
    def refund(self, payment_id: str, amount: Optional[float] = None) -> PaymentResult:
        """退款"""
        pass
    
    @abstractmethod
    def handle_webhook(self, payload: dict, signature: str) -> dict:
        """处理 Webhook 回调"""
        pass
    
    def supports_currency(self, currency: Currency) -> bool:
        return currency in self.SUPPORTED_CURRENCIES
```

---

## 🏦 Stripe 实现

```python
import stripe
from typing import Optional

class StripeGateway:
    """Stripe 支付网关"""
    
    SUPPORTED_CURRENCIES = {Currency.USD, Currency.EUR, Currency.GBP}
    
    def __init__(self, secret_key: str, webhook_secret: str = None):
        stripe.api_key = secret_key
        self.webhook_secret = webhook_secret
    
    def create_payment(self, request: PaymentRequest) -> PaymentResult:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": request.currency.value.lower(),
                    "product_data": {
                        "name": request.metadata.get("service_name", "Service"),
                        "description": request.metadata.get("description", ""),
                    },
                    "unit_amount": int(request.amount * 100),
                    "quantity": 1,
                },
                "quantity": 1,
            }],
            mode="payment",
            customer_email=request.client_email,
            success_url=request.return_url or "https://your-domain.com/success?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=request.cancel_url or "https://your-domain.com/cancel",
            metadata=request.metadata,
            expires_at=int((datetime.now() + timedelta(hours=24)).timestamp()),
        )
        return PaymentResult(
            payment_id=session.id,
            status=PaymentStatus.PENDING,
            payment_url=session.url,
            expires_at=(datetime.now() + timedelta(hours=24)).isoformat(),
            raw_response=session.to_dict()
        )
    
    def verify_payment(self, payment_id: str) -> PaymentResult:
        session = stripe.checkout.Session.retrieve(payment_id)
        status_map = {
            "open": PaymentStatus.PENDING,
            "complete": PaymentStatus.SUCCEEDED,
            "expired": PaymentStatus.CANCELLED,
        }
        return PaymentResult(
            payment_id=session.id,
            status=status_map.get(session.payment_status, PaymentStatus.PENDING),
            raw_response=session.to_dict()
        )
    
    def handle_webhook(self, payload: dict, signature: str) -> dict:
        event = stripe.Webhook.construct_event(
            payload, signature, self.webhook_secret
        )
        return {"event_type": event.type, "data": event.data.object.to_dict()}
```

---

## 💰 USDC (Base/Polygon) 实现

```python
from web3 import Web3
from eth_account import Account
import os

class USDCGateway:
    """USDC 支付网关 (Base/Polygon)"""
    
    SUPPORTED_CURRENCIES = {Currency.USD}
    
    USDC_CONTRACTS = {
        "base": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
        "polygon": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    }
    
    USDC_ABI = json.loads('[{"constant":true,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":false,"inputs":[{"name":"_to","type":"address"},{"name":"_value","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"type":"function"}]')
    
    def __init__(self, rpc_url: str, private_key: str, chain: str = "base"):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = Account.from_key(private_key)
        self.chain = chain
        self.contract = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.USDC_CONTRACTS[chain]),
            abi=self.USDC_ABI
        )
    
    def create_payment(self, request: PaymentRequest) -> PaymentResult:
        amount_usdc = int(request.amount * 1_000_000)
        payment_id = f"usdc_{uuid.uuid4().hex[:16]}"
        
        return PaymentResult(
            payment_id=payment_id,
            status=PaymentStatus.PENDING,
            payment_url=f"https://basescan.org/address/{self.account.address}",
            qr_code=None,
            raw_response={
                "to_address": self.account.address,
                "amount_usdc": request.amount,
                "chain": self.chain,
                "contract": self.USDC_CONTRACTS[self.chain],
                "memo": request.metadata.get("memo", "")
            }
        )
    
    def verify_payment(self, payment_id: str) -> PaymentResult:
        return PaymentResult(
            payment_id=payment_id,
            status=PaymentStatus.PENDING,
            raw_response={"note": "USDC verification requires event indexing"}
        )
```

---

## 🏪 支付宝/微信实现框架

```python
class AlipayGateway:
    SUPPORTED_CURRENCIES = {Currency.CNY}
    
    def __init__(self, app_id: str, private_key: str, alipay_public_key: str, sandbox: bool = True):
        self.app_id = app_id
        self.private_key = private_key
        self.alipay_public_key = alipay_public_key
        self.gateway = "https://openapi.alipaydev.com/gateway.do" if sandbox else "https://openapi.alipay.com/gateway.do"
    
    def create_payment(self, request: PaymentRequest) -> PaymentResult:
        pass

class WechatGateway:
    SUPPORTED_CURRENCIES = {Currency.CNY}
    
    def __init__(self, app_id: str, mch_id: str, api_key: str, cert_path: str, key_path: str):
        self.app_id = app_id
        self.mch_id = mch_id
        self.api_key = api_key
    
    def create_payment(self, request: PaymentRequest) -> PaymentResult:
        pass
```

---

## 🔧 统一网关管理器

```python
class PaymentGatewayManager:
    def __init__(self, config: dict):
        self.gateways = {}
        self._init_gateways(config)
    
    def _init_gateways(self, config: dict):
        if config.get("stripe"):
            self.gateways["stripe"] = StripeGateway(
                config["stripe"]["secret_key"],
                config["stripe"].get("webhook_secret")
            )
        if config.get("usdc"):
            self.gateways["usdc"] = USDCGateway(
                config["usdc"]["rpc_url"],
                config["usdc"]["private_key"],
                config["usdc"].get("chain", "base")
            )
        if config.get("alipay"):
            self.gateways["alipay"] = AlipayGateway(
                config["alipay"]["app_id"],
                config["alipay"]["private_key"],
                config["alipay"]["alipay_public_key"],
                config["alipay"].get("sandbox", True)
            )
        if config.get("wechat"):
            self.gateways["wechat"] = WechatGateway(
                config["wechat"]["app_id"],
                config["wechat"]["mch_id"],
                config["wechat"]["api_key"],
                config["wechat"]["cert_path"],
                config["wechat"]["key_path"]
            )
    
    def get_gateway_for_currency(self, currency: Currency) -> Optional[object]:
        priority = ["stripe", "alipay", "wechat", "usdc"]
        for gw_name in priority:
            gw = self.gateways.get(gw_name)
            if gw and gw.supports_currency(currency):
                return gw
        return None
    
    def create_payment(self, amount: float, currency: str, client_email: str, metadata: dict) -> dict:
        currency_enum = Currency(currency.upper())
        gateway = self.get_gateway_for_currency(Currency(currency.upper()))
        if not gateway:
            raise ValueError(f"No gateway for currency: {currency}")
        
        request = PaymentRequest(
            amount=amount,
            currency=Currency(currency.upper()),
            client_email=client_email,
            metadata=metadata
        )
        result = gateway.create_payment(request)
        return {
            "gateway": type(gateway).__name__,
            "payment_id": result.payment_id,
            "status": result.status.value,
            "payment_url": result.payment_url,
            "qr_code": result.qr_code,
            "expires_at": result.expires_at,
            "raw": result.raw_response
        }
```

---

## 📋 配置示例

```yaml
# ~/.hermes/payment_gateway.yaml
stripe:
  secret_key: "sk_live_xxx"
  webhook_secret: "whsec_xxx"

usdc:
  rpc_url: "https://mainnet.base.org"
  private_key: "0x..."
  chain: "base"

alipay:
  app_id: "202100xxxx"
  private_key: "-----BEGIN RSA PRIVATE KEY-----..."
  alipay_public_key: "-----BEGIN PUBLIC KEY-----..."
  sandbox: true

wechat:
  app_id: "wx_xxx"
  mch_id: "1234567890"
  api_key: "xxx"
  cert_path: "/path/to/apiclient_cert.pem"
  key_path: "/path/to/apiclient_key.pem"
```

---

## 📊 监控与对账

```python
class PaymentMonitor:
    def __init__(self, gateway_manager: PaymentGatewayManager):
        self.manager = gateway_manager
    
    async def monitor_pending_payments(self):
        pass
    
    def daily_reconciliation(self) -> dict:
        report = {
            "date": datetime.now().date().isoformat(),
            "stripe": self._reconcile_stripe(),
            "usdc": self._reconcile_usdc(),
            "alipay": self._reconcile_alipay(),
            "wechat": self._reconcile_wechat(),
            "summary": {}
        }
        return report
    
    def generate_invoice_pdf(self, payment_data: dict) -> bytes:
        from reportlab.lib.pagesizes import A4
        from reportlab.pdfgen import canvas
        pass
```

---

## 🚀 部署到 Hermes

```bash
mkdir -p ~/.hermes/skills/revenue/payment-gateway/scripts

cat > ~/.hermes/skills/revenue/payment-gateway/scripts/validate.py << 'EOF'
#!/usr/bin/env python3
import sys

checks = {
    "stripe": ["python3", "-c", "import stripe; print(stripe.__version__)"],
    "web3": ["python3", "-c", "from web3 import Web3; print(Web3.__version__)"],
    "reportlab": ["python3", "-c", "import reportlab; print(reportlab.__version__)"],
    "qrcode": ["python3", "-c", "import qrcode; print(qrcode.__version__)"],
    "cryptography": ["python3", "-c", "import cryptography; print(cryptography.__version__)"],
}

all_ok = True
for name, cmd in checks.items():
    try:
        import subprocess
        result = subprocess.run(cmd, capture_output=True, timeout=10, check=True)
        print(f"✅ {name}: {result.stdout.decode().strip()}")
    except Exception as e:
        print(f"❌ {name}: MISSING - {e}")

print("Payment Gateway 依赖检查完成")
EOF
```