# PyInstaller Frozen 模式路径锚定模式

> 单文件 exe 打包后，`__file__` 指向临时解压目录 (`_MEIPASS`)，配置/资源若跟着写进去会每次重启丢失、用户也改不到。

## 核心模式

```python
import sys
from pathlib import Path

def _runtime_root() -> Path:
    """确定运行时根目录。

    PyInstaller 单文件模式下 __file__ 指向临时解压目录（_MEIPASS），
    配置若跟着写进去，每次重启都会丢、用户也改不到。
    打包后必须锚定到 exe 所在目录。
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parents[1]


CONFIG_PATH = _runtime_root() / "config.json"
```

## 适用场景

| 场景 | 正确锚定点 |
|---|---|
| 配置文件读写 | `exe_dir / "config.json"` |
| 资源文件读取 | `exe_dir / "assets" / "xxx.png"` |
| 日志文件落盘 | `exe_dir / "logs" / "app.log"` |
| 用户数据目录 | `exe_dir / "data"` |

## 常见错误

| 错误写法 | 后果 |
|---|---|
| `CONFIG_PATH = Path(__file__).parents[1] / "config.json"` | 打包后写入 `_MEIPASS` 临时目录，重启即丢 |
| `Path(__file__).parent / "assets"` | 读取不到打包进 exe 的资源 |
| `Path.cwd()` | 用户从任意目录启动 exe 时不定 |

## 验证方法

```python
# 模拟 frozen 态验证
import sys
sys.frozen = True
sys.executable = r"D:\dist_probe\ImgBatchTool.exe"
import importlib
import backend.config as cfgmod
importlib.reload(cfgmod)
assert str(cfgmod.CONFIG_PATH).endswith("dist_probe/config.json")
print("✅ 锚定到 exe 所在目录")
```

## flet pack 特有注意

- `flet pack` 打包时会自动把 `~/.flet/client/flet-desktop-full-<ver>/` 整个带进单文件
- `--collect-all flet` 只收集 Python 包，**收不到桌面客户端二进制**
- 裸 PyInstaller + `--collect-all flet` 产出的 exe **换机器必崩**
- 体积 < 30MB 说明客户端没打进去，视为构建失败

## 相关工具

- `build/build.py` —— 使用 `flet pack` 的标准打包脚本
- `scripts/verify_frozen_paths.py` —— 可选验证脚本