# pyxianyu 核心 API 速查

## XianyuClient
```python
from pyxianyu import XianyuClient

# 初始化
client = XianyuClient(cookies=cookie_dict, device_id="auto")

# 核心方法
client.build_mtop_params(api_name, version, data)  # 构造 MTOP 请求参数
client.build_signed_form(params)  # 签名表单
client.post_json(api_name, version, data)  # 发送 JSON 请求
client.parse_json_response(response)  # 解析响应
client.get_cookie_value(name)  # 获取 Cookie 值
client.clear_conflicting_cookies()  # 清理冲突 Cookie
client.ensure_api_success(response)  # 校验 API 成功
```

## SearchApi
```python
from pyxianyu.apis import SearchApi

search_api = SearchApi(client)

# 搜索商品
result = await search_api.search_items(
    keyword="关键词",
    page_number=1,
    rows_per_page=20,
    sort_type="want_count"  # want_count/view_count/price/publish_time
)
```

## ItemApi
```python
from pyxianyu.apis import ItemApi

item_api = ItemApi(client)

# 获取商品详情
detail = await item_api.get_item_detail(item_id)

# 发布商品
await item_api.publish_item(payload)

# 编辑商品
await item_api.edit_item(item_id, payload)

# 下架商品
await item_api.downshelf_item(item_id)

# 擦亮商品
await item_api.polish_item(item_id)
```

## XianyuLive (WebSocket 长连接)
```python
from pyxianyu.xianyu_live import XianyuLive

live = XianyuLive(client)

# 连接
await live.connect()

# 发送消息
await live.send_msg(conversation_id, to_user_id, "消息内容")

# 监听消息
async for msg in live.messages():
    print(msg)
```

## 常用数据结构

### 搜索结果 Item
```python
{
    "itemId": "123456",
    "title": "商品标题",
    "price": "9.9",
    "originalPrice": "29.9",
    "sellerNick": "卖家昵称",
    "wantCount": 156,
    "viewCount": 2340,
    "publishTime": "2024-12-01T10:00:00",
    "area": "浙江/杭州",
    "tags": ["标签1", "标签2"],
    "picUrl": "https://...",
    "images": [{"url": "..."}],
    "itemType": "virtual"  # 虚拟商品标识
}
```

### 发布 Payload 关键字段
```python
{
    "title": "商品标题",
    "desc": "商品描述",
    "price": "990",  # 分为单位
    "originalPrice": "2990",
    "categoryId": "50101000",
    "images": ["image_url1", "image_url2"],
    "skuList": [
        {"name": "基础版", "price": 990, "stock": 999},
        {"name": "进阶版", "price": 1990, "stock": 999}
    ],
    "tags": ["标签1", "标签2"],
    "area": "浙江/杭州",
    "deliveryType": "virtual"
}
```