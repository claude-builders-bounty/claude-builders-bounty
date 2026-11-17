---
name: invoice-manager
description: 发票/收款管理器：多渠道开票/收款/对账/催款，支持 Stripe/支付宝/微信/USDC，零 Token 成本
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [invoice, payment, billing, stripe, alipay, wechat, usdc, accounting, revenue]
    related_skills: [seo-auditor, content-writer, lead-generator, lead-generator]
    requires_toolsets: [terminal, web, file, web_search]
---

# 发票/收款管理器

**核心使命**：多渠道统一开票、收款、对账、催款，支持 Stripe/支付宝/微信/USDC，实现**零 Token 成本**的资金闭环。

---

## 🎯 核心能力

| 功能 | 描述 | 支持渠道 |
|------|------|----------|
| **创建发票/支付链接** | 根据金额/币种/客户生成支付链接/二维码 | Stripe/支付宝/微信/USDC |
| **支付状态轮询** | 实时/定时检查支付状态 | Webhook + 定时轮询双保险 |
| **自动对账** | 核对平台收入/支付记录/手续费 | 定时任务 + 手动触发 |
| **自动催款** | 超期未付自动发送提醒 | 邮件/站内信/短信 |
| **发票归档** | PDF 生成/存储/检索/税务合规 | 本地存储 + 云端备份 |
| **收益统计** | 日/周/月/年聚合/趋势/预测 | 仪表盘 + 导出报表 |

---

## 💰 多渠道支付接口抽象

```python
class PaymentGateway:
    """统一支付网关：Stripe/支付宝/微信/USDC"""
    
    SUPPORTED_CURRENCIES = {
        "USD": ["stripe", "usdc"],
        "CNY": ["alipay", "wechat"],
        "EUR": ["stripe"],
        "GBP": ["stripe"],
    }
    
    def __init__(self, config: dict):
        self.config = config
        self.stripe_client = self._init_stripe() if config.get("stripe") else None
        self.alipay_client = self._init_alipay() if config.get("alipay") else None
        self.wechat_client = self._init_wechat() if config.get("wechat") else None
    
    def create_payment_link(self, amount: float, currency: str, 
                           client_email: str, metadata: dict) -> dict:
        """
        创建支付链接/二维码
        :return: {"payment_url": "...", "qr_code": "...", "payment_id": "...", "expires_at": "..."}
        """
        currency = currency.upper()
        gateway = self._select_gateway(currency)
        
        if gateway == "stripe":
            return self._stripe_checkout(amount, currency, client_email, metadata)
        elif gateway == "alipay":
            return self._alipay_wap_pay(amount, currency, client_email, metadata)
        elif gateway == "wechat":
            return self._wechat_h5_pay(amount, currency, client_email, metadata)
        elif gateway == "usdc":
            return self._usdc_address(amount, currency, metadata)
        else:
            raise ValueError(f"Unsupported currency: {currency}")
    
    def _select_gateway(self, currency: str) -> str:
        """根据币种和配置选择最优网关"""
        available = self.SUPPORTED_CURRENCIES.get(currency, [])
        for gw in ["stripe", "alipay", "wechat", "usdc"]:
            if gw in available and getattr(self, f"{gw}_client", None):
                return gw
        raise ValueError(f"No gateway available for {currency}")
    
    def verify_payment(self, payment_id: str) -> dict:
        """验证支付状态"""
        # 实现各网关的支付验证
        pass
    
    def refund(self, payment_id: str, amount: float = None) -> dict:
        """退款"""
        pass
    
    def webhook_handler(self, payload: dict, signature: str) -> dict:
        """处理 Webhook 回调"""
        pass
```

---

## 📋 发票标准化

### 发票数据模型
```json
{
  "invoice_id": "INV-20261004-001",
  "mission_id": "MISSION-20261004-001",
  "client": {
    "name": "Acme Corp",
    "email": "billing@acme.com",
    "tax_id": "US12345678",
    "address": "123 Main St, San Francisco, CA 94102"
  },
  "items": [
    {
      "description": "SEO Audit Service",
      "quantity": 1,
      "unit_price": 150,
      "currency": "USD",
      "tax_rate": 0
    }
  ],
  "subtotal": 150,
  "tax": 0,
  "total": 150,
  "currency": "USD",
  "status": "draft|sent|paid|overdue|cancelled|refunded",
  "payment_method": "stripe",
  "payment_id": "pi_xxx",
  "issued_at": "2026-10-04T09:00:00Z",
  "due_date": "2026-10-18T23:59:59Z",
  "paid_at": null,
  "paid_amount": 0,
  "pdf_url": "https://storage.xxx/invoice-INV-20261004-001.pdf"
}
```

### 发票状态机
```
draft → sent → paid → completed
  ↓       ↓
cancelled  overdue → cancelled
              ↓
            refunded
```

---

## 🔄 自动化流程

### 1. 开票流程
```
任务完成 → 生成发票数据 → 生成 PDF → 发送邮件/上传平台 → 记入账本
```

### 2. 收款监控
```
创建支付链接 → 发送给客户 → Webhook/轮询监控 → 支付成功 → 更新状态 → 发送收据 → 记入收益
```

### 3. 对账流程（每日 02:00）
```
拉取平台交易记录 ↔ 本地发票记录 → 差异标记 → 人工/自动修正 → 生成对账单
```

### 3. 催款流程
```
发票过期 3天 → 自动发送提醒邮件
发票过期 7天 → 发送第二次提醒 + 电话/短信
发票过期 14天 → 标记坏账风险 → 人工介入
发票过期 30天 → 标记坏账 → 税务处理
```

---

## 📊 统计指标

| 指标 | 计算方式 | 告警阈值 |
|------|----------|----------|
| 应收账款 (AR) | Σ 未收发票金额 | > $10k 告警 |
| 平均收款天数 (DSO) | Σ (收款日-开票日) * 金额 / Σ 金额 | > 30 天告警 |
| 收款率 | 已收金额 / 应收总额 | < 80% 告警 |
| 坏账率 | 坏账金额 / 总开票金额 | > 5% 告警 |
| 手续费率 | 手续费 / 总流水 | > 3% 优化渠道 |

---

## 📁 文件结构

```
invoices/
  INV-20261004-001/
    invoice.json          # 发票数据
    invoice.pdf           # PDF 发票
    qr_code.png           # 支付二维码
    payment_proof.json    # 支付凭证
  ledger.jsonl            # 流水账
  revenue.jsonl           # 收入记录
  reconciliation/         # 对账单
    2026-10-04-reconciliation.json
  reports/
    monthly-2026-10.json
    quarterly-2026-Q4.json
```

---

## 🛠️ 实现优先级

| 优先级 | 功能 | 预估工时 |
|--------|------|----------|
| P0 | Stripe Checkout 集成 | 4h |
| P0 | USDC 地址生成/验证 | 2h |
| P1 | 支付宝当面付/网页支付 | 8h |
| P1 | 微信 H5/JSAPI 支付 | 8h |
| P1 | PDF 发票生成 | 4h |
| P1 | 邮件发送/模板 | 2h |
| P2 | 对账自动化 | 4h |
| P2 | 催款自动化 | 2h |
| P2 | 仪表盘/报表 | 4h |

---

## 🔗 协作 Skill

| Skill | 协作方式 |
|-------|----------|
| `seo-auditor` / `content-writer` / `lead-generator` | 任务完成 → 自动开票 |
| `lead-generator` | 线索成交 → 自动开票 |
| `prompt-templates` | 使用标准发票/催款模板 |
| `RuntimeGuard` | 支付处理超时/异常保护 |

---

## 🚀 部署到 Hermes

```bash
mkdir -p ~/.hermes/skills/revenue/invoice-manager/scripts

# 验证脚本
cat > ~/.hermes/skills/revenue/invoice-manager/scripts/validate.py << 'EOF'
#!/usr/bin/env python3
import shutil, subprocess, sys

checks = {
    "python3": ["python3", "--version"],
    "stripe": ["python3", "-c", "import stripe; print(stripe.__version__)"],
    "reportlab": ["python3", "-c", "import reportlab; print(reportlab.__version__)"],
    "qrcode": ["python3", "-c", "import qrcode; print(qrcode.__version__)"],
    "jinja2": ["python3", "-c", "import jinja2; print(jinja2.__version__)"],
}

all_ok = True
for name, cmd in [
    ("python3", ["python3", "--version"]),
    ("reportlab", ["python3", "-c", "import reportlab; print(reportlab.__version__)"]),
    ("qrcode", ["python3", "-c", "import qrcode; print(qrcode.__version__)"]),
    ("jinja2", ["python3", "-c", "import jinja2; print(jinja2.__version__)"]),
]:
    try:
        import subprocess
        subprocess.run(cmd, capture_output=True, timeout=10, check=True)
        print(f"✅ {name}: OK")
    except:
        print(f"❌ {name}: MISSING (可后续安装)")

print("环境检查完成")
EOF
```