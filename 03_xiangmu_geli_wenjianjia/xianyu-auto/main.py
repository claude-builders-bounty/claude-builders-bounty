#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
闲鱼自动化运营系统 - 主入口
功能：初始化客户端、配置、启动各模块主循环
"""

import asyncio
import logging
import sys
import os
import yaml
from pathlib import Path
from typing import Dict, Any

# 添加项目路径 - 必须在其他导入之前
WORKFLOW_SRC = r"D:\Ai\Agent\xiangmu\xianyu_agent_workflow\src"
if WORKFLOW_SRC not in sys.path:
    sys.path.insert(0, WORKFLOW_SRC)

# 添加本地脚本路径
LOCAL_SCRIPTS = str(Path(__file__).parent / "scripts")
if LOCAL_SCRIPTS not in sys.path:
    sys.path.insert(0, LOCAL_SCRIPTS)

from scripts.core.client import XianyuClientWrapper, create_client_from_env
from scripts.listing.auto_listing import AutoListing
from scripts.delivery.auto_delivery import AutoDelivery

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/xianyu.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class XianyuAutomation:
    """闲鱼自动化主控制器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client: XianyuClientWrapper = None
        self.auto_listing: AutoListing = None
        self.auto_delivery: AutoDelivery = None
        self._running = False
        
    async def initialize(self):
        """初始化所有组件"""
        logger.info("正在初始化闲鱼自动化运营系统...")
        
        # 1. 初始化客户端
        logger.info("正在初始化客户端...")
        self.client = create_client_from_env()
        await self.client.initialize()
        logger.info("客户端初始化完成")
        
        # 2. 初始化各模块
        logger.info("正在初始化各模块...")
        self.auto_listing = AutoListing(self.client.client, self.config)
        self.auto_delivery = AutoDelivery(self.client.client, self.config)
        logger.info("模块初始化完成")
        
        # 确保日志目录存在
        Path('logs').mkdir(exist_ok=True)
        
        self._running = True
        logger.info("初始化完成")
        
    async def run_listing_cycle(self):
        """商品管理周期"""
        logger.info("启动商品管理周期")
        while self._running:
            try:
                await self.auto_listing.manage_listings()
            except Exception as e:
                logger.error(f"商品管理周期异常: {e}")
            await asyncio.sleep(self.config.get('runtime', {}).get('check_interval', 300))
            
    async def run_delivery_cycle(self):
        """发货处理循环"""
        logger.info("启动发货处理循环")
        while self._running:
            try:
                await self.auto_delivery.process_orders()
            except Exception as e:
                logger.error(f"发货循环异常: {e}")
            await asyncio.sleep(self.config.get('runtime', {}).get('check_interval', 300))
            
    async def run_monitor_cycle(self):
        """监控循环"""
        logger.info("启动监控循环")
        while self._running:
            try:
                # 监控逻辑：检查系统健康、API响应等
                logger.debug("监控检查...")
            except Exception as e:
                logger.error(f"监控异常: {e}")
            await asyncio.sleep(60)
            
    async def run_health_check(self):
        """健康检查循环"""
        logger.info("启动健康检查循环")
        while self._running:
            try:
                # 健康检查：token状态、连接状态等
                from framework.xianyu_session import sync_server_token
                sync_server_token(self.client.client)
                logger.debug("Token同步完成")
            except Exception as e:
                logger.error(f"健康检查异常: {e}")
            await asyncio.sleep(300)
            
    async def run_reply_cycle(self):
        """自动回复循环（占位，待实现）"""
        logger.info("启动消息回复循环")
        while self._running:
            try:
                # TODO: 实现自动回复逻辑
                pass
            except Exception as e:
                logger.error(f"回复循环异常: {e}")
            await asyncio.sleep(self.config.get('runtime', {}).get('rate_limit_delay', 5))
            
    async def start(self):
        """启动所有循环"""
        logger.info("启动闲鱼自动化运营...")
        
        # 创建所有任务
        tasks = [
            asyncio.create_task(self.run_listing_cycle()),
            asyncio.create_task(self.run_delivery_cycle()),
            asyncio.create_task(self.run_monitor_cycle()),
            asyncio.create_task(self.run_health_check()),
            asyncio.create_task(self.run_reply_cycle()),
        ]
        
        try:
            await asyncio.gather(*tasks)
        except KeyboardInterrupt:
            logger.info("收到中断信号，正在停止...")
            self._running = False
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            logger.error(f"主循环异常: {e}")
            raise
        finally:
            logger.info("闲鱼自动化运营已停止")


class ConfigDict(dict):
    """支持属性访问的字典"""
    def __getattr__(self, name):
        try:
            return self[name]
        except KeyError:
            raise AttributeError(f"'ConfigDict' object has no attribute '{name}'")
    
    def __setattr__(self, name, value):
        self[name] = value


def load_config() -> ConfigDict:
    """加载配置文件"""
    config_path = Path('config.yaml')
    if not config_path.exists():
        # 复制示例配置
        example_path = Path('config/config.example.yaml')
        if example_path.exists():
            import shutil
            shutil.copy(example_path, config_path)
            logger.warning(f"配置文件不存在，已从示例复制: {config_path}")
            logger.warning("请编辑 config.yaml 填入真实 Cookie 后重新运行")
        else:
            raise FileNotFoundError("找不到配置文件 config.yaml 和示例文件")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 递归转换嵌套 dict
    def convert(obj):
        if isinstance(obj, dict):
            return ConfigDict({k: convert(v) for k, v in obj.items()})
        elif isinstance(obj, list):
            return [convert(item) for item in obj]
        return obj
    
    config = convert(config)
    
    # 验证必要配置
    cookie = config.account.get('cookie', '')
    if not cookie:
        logger.error("配置文件中未设置 Cookie (account.cookie)")
        logger.error("请编辑 config.yaml 填入完整的闲鱼 Cookie 字符串")
        sys.exit(1)
        
    return config


async def main():
    """主函数"""
    logger.info("=" * 50)
    logger.info("闲鱼自动化运营系统启动")
    logger.info("=" * 50)
    
    # 加载配置
    config = load_config()
    
    # 创建并启动自动化
    automation = XianyuAutomation(config)
    await automation.initialize()
    await automation.start()


if __name__ == "__main__":
    # Windows 事件循环策略
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("用户中断，退出")
    except Exception as e:
        logger.error(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)