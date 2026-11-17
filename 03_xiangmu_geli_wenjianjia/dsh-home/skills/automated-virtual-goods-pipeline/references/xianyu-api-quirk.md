# Xianyu API Quirks & Version-Specific Notes

## pyxianyu 1.0.0 (Current)

### Authentication
- Cookie must contain: `_m_h5_tk`, `_m_h5_tk_enc`, `cookie2`, `t`, `cna`, `xlly_s`
- Token auto-refresh works but fails silently on 401 — monitor logs for `XianyuApiError: 401`
- Cookie expiry ~30 days; refresh via headless browser (Playwright) if needed

### Rate Limits
- Search API: ~30 req/min per IP/account (exceed → 429)
- Publish API: ~10 req/min (exceed → "风控拦截")
- WebSocket: 1 connection per account; reconnect with exponential backoff (2s, 4s, 8s, max 60s)

### Error Codes
| Code | Meaning | Action |
|------|---------|--------|
| 400600001 | Message rate limit | Exponential backoff retry |
| 401 | Cookie expired | Refresh cookie |
| 403 | Forbidden (risk control) | Reduce frequency, check sensitive words |
| FAIL_BIZ_PC_NOT_SUPPORT_PUBLISH_OR_EDIT | Virtual goods not allowed via PC publish | Use mobile API or FishOps CSV |
| IDLEITEM_POLISH_AGAIN | Already polished today | Skip, it's idempotent success |

### Search API Quirks
- `sort_type`: `want_count` (想要数), `view_count` (浏览), `publish_time` (发布时间), `price` (价格)
- `rows_per_page` max 20; pagination via `page_number`
- Results include `itemId`, `title`, `price`, `wantCount`, `viewCount`, `sellerNick`, `tags`, `picUrl`, `publishTime`

### Publish API Flow
1. `prepublish_check()` — validate account/item
2. `preget()` — get publish params (category, props, etc.)
3. `publish_item(payload)` — submit; payload must include images uploaded via `upload_media()`
4. Virtual goods: set `deliveryType: "virtual"` and category `50101000`

### WebSocket (XianyuLive)
- Connect via `XianyuLive(client)` → handles sign + protobuf
- Events: `new_order`, `chat_message`, `order_status_change`
- Must handle reconnection; use `send_msg()` for replies
- Message types: text, image (base64)

## goofish-cli MCP Server (v1.30.0)

### Available Tools (verified via tools/list)
| Tool | Required Args | Notes |
|------|---------------|-------|
| `auth_login` | (none) | Import login state from browser |
| `auth_status` | (none) | Check login validity |
| `auth_reset_guard` | (none) | Manual risk control unlock |
| `media_upload` | `path` | Upload image, returns `{url, width, height, size}` |
| `category_recommend` | `title` | AI category detection |
| `item_publish` | `title`, `desc`, `price` | **Must use `images_json` + `category_json`** |
| `item_get` | `item_id` | Get item details (API path) |
| `item_view` | `item_id` | Get item details (browser path, anti-risk) |
| `item_delete` | `item_id` | Take down item |
| `item_list` | (none) | List own items |
| `search_items` | `query` | Search items (browser path, anti-risk) |
| `location_default` | (none) | Get default publish location |
| `message_list_chats` | (none) | List recent chats |
| `message_history` | `cid` | Get chat history |
| `message_send` | `cid`, `toid`, `text` | Send message |
| `message_watch` | (none) | Long-poll IM events (JSONL stdout) |

### item_publish Parameter Format (CRITICAL)
```json
{
  "title": "商品标题",
  "desc": "商品描述 (NOT description!)",
  "price": 9.9,
  "images_json": "[{\"url\": \"https://...\", \"width\": 800, \"height\": 800}]",
  "category_json": "{\"cat_id\": \"50101000\", \"cat_name\": \"模板\", \"channel_cat_id\": \"50101000\", \"tb_cat_id\": \"50101000\"}",
  "delivery": "无需邮寄",
  "post_price": 0,
  "can_self_pickup": true
}
```
**Key differences from pyxianyu:**
- `desc` NOT `description`
- `images_json` stringified array of objects with `url`+`width`+`height` (NOT `images` array of URLs)
- `category_json` stringified object with `cat_id`/`cat_name`/`channel_cat_id`/`tb_cat_id` (NOT simple string)
- `delivery`: "无需邮寄" for virtual goods

### Common Errors
| Error | Cause | Fix |
|-------|-------|-----|
| "图片文件不存在或为空" | `images_json` missing width/height | Use `media_upload` first, include full object |
| "已上传图片必须包含 url、width、height" | Same as above | Include all 3 fields |
| "已确认类目必须包含 cat_id/cat_name/channel_cat_id/tb_cat_id" | `category_json` incomplete | Provide all 4 fields |
| "登录态失效：FAIL_SYS_TOKEN_EXOIRED::令牌过期" | Cookie expired | Refresh XIANYU_COOKIE |
| "发布必须有 1–9 张图片" | No images provided | At least 1 image required |

### Version History
| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-08 | pyxianyu initial release; full HTTP + WS coverage |
| 1.30.0 | 2026-10 | goofish-cli MCP server released; full MCP toolset |
| 0.x | 2025 | Early prototypes; breaking changes |

### Testing Checklist
- [ ] Cookie valid (search returns results)
- [ ] Search with keywords returns expected fields
- [ ] Publish dry-run (FishOps CSV) generates valid file
- [ ] WebSocket connects and receives test message
- [ ] Card code reserve/commit/rollback works
- [ ] Sensitive word replacement triggers on known flags
- [ ] goofish-cli media_upload returns url+width+height
- [ ] goofish-cli item_publish works with images_json + category_json format
- [ ] message_list_chats + message_history polling works for order detection