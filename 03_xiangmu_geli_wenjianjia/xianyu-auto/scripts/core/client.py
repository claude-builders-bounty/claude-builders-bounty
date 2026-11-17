# -*- coding: utf-8 -*-
"""
闲鱼客户端封装
统一管理 pyxianyu 客户端初始化、Cookie 管理、Token 同步
"""

import os
import json
import asyncio
from typing import Dict, Optional, Any
from pyxianyu import XianyuClient
from pyxianyu.apis import SearchApi, ItemApi, UserApi
from pyxianyu.core.exceptions import XianyuApiError

from framework.xianyu_session import (
    sync_server_token,
    call_with_token_refresh,
    is_recoverable_token_error
)


class XianyuClientWrapper:
    """闲鱼客户端包装器，提供高级封装"""
    
    def __init__(self, cookie_str: str, device_id: str = "auto"):
        self.cookie_str = cookie_str
        self.cookie_dict = self._parse_cookie(cookie_str)
        self.client = XianyuClient(cookies=self.cookie_dict, device_id="auto")
        self._initialized = False
    
    def _parse_cookie(self, cookie_str: str) -> dict:
        """解析 Cookie 字符串为字典"""
        cookie_dict = {}
        for part in cookie_str.split(";"):
            part = part.strip()
            if "=" in part:
                k, v = part.split("=", 1)
                cookie_dict[k.strip()] = v.strip()
        return cookie_dict
    
    async def initialize(self):
        """初始化客户端，同步 token"""
        from framework.xianyu_session import sync_server_token
        sync_server_token(self.client)
        self._initialized = True
    
    @property
    def search_api(self):
        from pyxianyu.apis import SearchApi
        if not hasattr(self, '_search_api'):
            from pyxianyu.apis import SearchApi
            self._search_api = SearchApi(self.client)
        return self._search_api
    
    @property
    def item_api(self):
        from pyxianyu.apis import ItemApi
        if not hasattr(self, '_item_api'):
            from pyxianyu.apis import ItemApi
            self._item_api = ItemApi(self.client)
        return self._item_api
    
    @property
    def user_api(self):
        from pyxianyu.apis import UserApi
        if not hasattr(self, '_user_api'):
            from pyxianyu.apis import UserApi
            self._user_api = UserApi(self.client)
        return self._user_api
    
    async def search_items(self, keyword: str, page: int = 1, per_page: int = 20) -> dict:
        """搜索商品（带自动重试）"""
        from framework.xianyu_session import call_with_token_refresh
        from pyxianyu.apis import SearchApi
        
        api = self.search_api
        return await call_with_token_refresh(
            self.client,
            self.client.search_api.search_items,
            keyword=keyword,
            page_number=1,
            rows_per_page=20
        )
    
    async def get_item_detail(self, item_id: str) -> dict:
        """获取商品详情（匿名可用）"""
        from framework.xianyu_session import call_with_token_refresh
        from pyxianyu.apis import ItemApi
        
        api = self.item_api
        from framework.xianyu_session import call_with_token_refresh
        return await call_with_token_refresh(
            self.client,
            self.item_api.get_item_info,
            str(item_id)
        )
    
    async def publish_item(self, payload: dict) -> dict:
        """发布商品"""
        from framework.xianyu_session import call_with_token_refresh
        return await call_with_token_refresh(
            self.client,
            self.item_api.publish_item,
            payload
        )
    
    async def send_message(self, conversation_id: str, content: str) -> dict:
        """发送消息"""
        # 实现发送消息逻辑
        pass
    
    async def get_orders(self, status: str = "WAIT_SELLER_SEND_GOODS") -> list:
        """获取待发货订单"""
        # 实现获取订单逻辑
        pass
    
    async def ship_order(self, order_id: str, logistics_company: str, tracking_no: str) -> dict:
        """发货"""
        pass
    
    async def reply_message(self, conversation_id: str, content: str) -> dict:
        """回复消息"""
        pass
    
    def update_cookie(self, cookie_str: str):
        """更新 Cookie"""
        self.cookie_str = cookie_str
        self.cookie_dict = self._parse_cookie(cookie_str)
        # 重新初始化客户端
        from pyxianyu import XianyuClient
        self.client = XianyuClient(cookies=self.cookie_dict, device_id="auto")


def create_client_from_env() -> 'XianyuClientWrapper':
    """从环境变量或配置文件创建客户端"""
    import os
    cookie = os.getenv('XIANYU_COOKIE', '')
    if not cookie:
        # 尝试从配置文件读取
        import yaml
        config_path = 'config.yaml'
        if os.path.exists(config_path):
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
                cookie = config.get('account', {}).get('cookie', '')
    
    if not cookie:
        raise ValueError("未找到 Cookie，请设置 XIANYU_COOKIE 环境变量或配置 config.yaml")
    
    return XianyuClientWrapper(cookie)
