"""
adapters - 平台适配器模块
统一接口适配各大赏金/竞赛平台
"""

from .base import (
    PlatformAdapter,
    TaskInfo,
    SubmissionResult,
    WithdrawalResult,
    AccountInfo,
    Track,
    TaskStatus,
    AdapterRegistry,
    register_adapter,
)

# 导入所有适配器以触发注册
from . import kaggle
from . import tianchi
from . import github_bounties
from . import github_bounties_public
from . import layer3
from . import dework

__all__ = [
    # 基类
    "PlatformAdapter",
    "TaskInfo",
    "SubmissionResult",
    "WithdrawalResult",
    "AccountInfo",
    "Track",
    "TaskStatus",
    "AdapterRegistry",
    "register_adapter",
    # 适配器 (通过导入自动注册)
    "kaggle",
    "tianchi",
    "github_bounties",
    "github_bounties_public",
    "layer3",
    "dework",
]

__version__ = "1.0.0"


def get_adapter(platform: str, credentials: dict, config: dict = None):
    """工厂函数：获取适配器实例"""
    return AdapterRegistry.create(platform, credentials, config)


def list_platforms() -> list[str]:
    """列出所有可用平台"""
    return AdapterRegistry.list_platforms()