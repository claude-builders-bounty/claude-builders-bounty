# Token Billing System (DeepSeek-V3 官方旗舰价格)

## Overview
`src/billing/TokenCounter` tracks token usage and cost **only for production orders** (after a real order is received). Debug/test runs are free.

## Pricing (人民币, DeepSeek-V3 官方旗舰)
| Type | Price |
|------|-------|
| Input | ¥0.001 / 1K tokens |
| Output | ¥0.002 / 1K tokens |

- **纯人民币结算，无汇率换算**
- 仅记接单后做单过程成本，调试/测试/空跑不计费

## API
```python
from src.billing import get_token_counter, TokenCounter

# Global singleton
c = get_token_counter()

# Switch to production mode (only then charges)
c.set_production_mode(True)

# Record usage (requires order_id, otherwise no charge)
cost = c.record(
    order_id="order_123",
    service="Excel函数公式编写",
    operation="reply_generation",
    input_tokens=1500,
    output_tokens=800
)

# Print summary
c.print_summary()
```

## Production vs Debug Mode
| Mode | `set_production_mode()` | `order_id` provided | Charges |
|------|------------------------|---------------------|---------|
| Debug | False | Any | ¥0 |
| Production | True | Yes | Yes |
| Production | True | No/empty | ¥0 |

## Integration with CSOrchestrator
`src/service_cs/cs_orchestrator.CSOrchestrator` automatically:
1. `set_order_context(order_id, service_name)` → `set_production_mode(True)`
2. `process_message()` → records token usage for each reply
3. `clear_order_context()` → `set_production_mode(False)` + prints summary

## Log Output
```
==================================================
💰 Token 计费汇总 (DeepSeek-V3 官方旗舰价格)
==================================================
会话时长: 12.3s
总请求数: 5
Input Tokens:  2,400
Output Tokens: 1,100
Total Tokens:  3,500
成本: ¥0.004700
按服务分摊: {'Excel函数公式编写': 0.0047}
按操作分摊: {'reply_generation': 0.0047}
按订单分摊: {'order_123': 0.0047}
==================================================
```

## Persistence
- Daily JSONL logs at `logs/billing/billing_YYYYMMDD.jsonl`
- Each record: timestamp, order_id, service, operation, input_tokens, output_tokens, cost_cny
- Survives process restarts (file-backed)

## Testing
```bash
cd D:/Ai/Agent/xiangmu/xianyu_pipeline
./venv/Scripts/python.exe -c "
from src.billing import get_token_counter
c = get_token_counter()
c.set_production_mode(True)
c.record('test_001', 'Excel函数公式编写', 'test', 1000, 500)
c.print_summary()
"
```
