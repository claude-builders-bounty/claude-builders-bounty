# Customer Service Module (`src/service_cs/`)

## Overview
Complete AI-powered customer service pipeline for Xianyu virtual goods. Handles the full conversation lifecycle: intent routing → pricing negotiation → fulfillment info → human handoff triggers.

## Components

### 1. `cs_orchestrator.py` - Main Loop
```python
orchestrator = CSOrchestrator()
orchestrator.set_order_context("order_123", "Excel函数公式编写")
reply = await orchestrator.process_message({"content": "50元成交？", "user_id": "buyer_001"})
orchestrator.clear_order_context()  # prints billing summary
```

### 2. `intent_router.py` - Intent Classification
Routes buyer messages to:
- `price_inquiry` - "多少钱？"
- `bargain` - "能不能便宜点？" / "50元成交"
- `delivery` - "发货快吗？"
- `refund` - "我想退款"
- `service_inquiry` / `service_scope` - 服务范围咨询
- `complaint` - 投诉/差评/威胁

### 3. `pricing_engine.py` - Dynamic Pricing
| Parameter | Rule |
|-----------|------|
| `floor` | Virtual: ≥70% list price; Physical: ≥breakeven |
| `max_discount` | High price (>200): 5-10%; Medium (50-200): 10-20%; Low (<50): 20-30% |
| `max_rounds` | Virtual: 2; Physical: 3 |
| Strategy | Gradient: 1st round 75% of total discount, 2nd round 25% |

### 4. `reply_generator.py` - Compliant Templates
Validated by `ServiceTalkValidator`:
- **No extreme words**: 秒发、全网最低、最好用、绝对没问题
- **Quantifiable promises only**: 24小时内自动发货、拍下后发网盘链接
- **Policy aligned with platform**: 质量问题可申请退款、未激活支持7天无理由
- **No unbounded promises**: 包教包会、永久售后

### 5. `human_handoff.py` - Escalation Triggers
| Trigger | Condition |
|---------|-----------|
| Amount threshold | <100: >50元; 100-500: >50% price; >500: >30% price |
| Risk keywords | 投诉、差评、平台介入、发票/法律、人身攻击 |
| Efficiency | max_rounds reached OR 3 rounds no progress |
| Refund dispute | 退款/纠纷关键词 detected |

## Integration Points

### With Billing
```python
# CSOrchestrator auto-records per-reply token cost in production mode
if self.counter.is_production() and self.current_order_id:
    self.counter.record(order_id, service, "reply_generation", 50, 30)
```

### With Phase 4 Delivery
Handoff context includes: order_id, service_name, buyer_intent, round_count, key_info (buyer_offer, refund_amount, keywords).

## Configuration (`config/pricing_rules.json`)
```json
{
  "services": {
    "Excel函数公式编写": {
      "floor_pct": 0.7,
      "max_discount_pct": 0.2,
      "max_rounds": 2,
      "list_price": 99
    }
  }
}
```

## Legal Compliance (from `config/human_handoff_rules.json`)
- **金额阈值**: 按客单价分级
- **高风险场景**: 投诉、差评、威胁平台介入、涉及发票/法律/工商、人身攻击
- **效率阈值**: 达到最大还价轮次仍未成交、连续 3 轮无实质进展

## Testing
```bash
cd D:/Ai/Agent/xiangmu/xianyu_pipeline
./venv/Scripts/python.exe -m src.service_cs.cs_orchestrator --test
```

Output:
```
>>> 买家: 多少钱？
<<< 客服: Excel函数公式编写 现价 99 元，拍下后系统自动发送网盘链接...
>>> 买家: 能不能便宜点？
<<< 客服: 亲，您想要什么价位呢？可以说个具体数字哦~
>>> 买家: 50元成交？
<<< 客服: 亲，您的问题需要专人处理，已为您转接人工客服...
>>> 买家: 发货快吗？
<<< 客服: 亲，拍下后系统自动发送网盘链接...
>>> 买家: 我想退款
<<< 客服: 亲，您的问题需要专人处理，已为您转接人工客服...
💰 Token 计费汇总: ¥0.000330
```
