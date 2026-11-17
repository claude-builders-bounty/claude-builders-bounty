# 执行层任务规格书：首批虚拟资源上架（2 个核心商品）

> 任务 ID：VR_FIRST_BATCH_20261031
> 创建时间：2026-10-31
> 适用 Profile：zhixing（执行层）
> 上游 Profile：legacy-session（决策层）
> 目标：跑通「脚本提取 → 差异化加工 → 百度网盘上传 → 闲鱼上架」完整闭环，上架 2 条核心商品

---

## 一、任务概况

| 项目 | 内容 |
|------|------|
| **商品 1** | Python 自动化办公脚本合集 50+ 实战案例 |
| **商品 2** | 素材加工自动化工具包（差异化引擎+使用指南） |
| **网盘** | 仅百度网盘（bdpan CLI，OAuth 通道） |
| **定价** | 商品 1：¥2.9 / 商品 2：¥3.9（参考竞品 Python 脚本 ¥1-1.28、工具类 ¥1-5） |
| **交付模式** | 永久分享链接 + 提取码，自动发货，无远程服务 |
| **预计上架数** | 2 条（先跑通闭环，再扩充至 5 条） |

---

## 二、已准备资产（只读，不可修改）

### 2.1 源代码目录
```
D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\xianyu_virtual_resource_first_batch\yuan_daima\
├── python_office_scripts\          # 商品 1 素材源
│   └── phase3_lister.py            # 仅作参考，实际脚本需从主仓库提取
├── material_processing_toolkit\    # 商品 2 素材源
│   ├── differentiator.py           # 差异化加工引擎核心
│   ├── factory_publish.py          # 发布管线（含上传/分享）
│   ├── netdisk_bdpan.py            # 百度网盘官方通道
│   ├── netdisk_baidu.py            # 备用通道
│   └── legal_gate.py               # 法律闸口
└── ops\                            # 运营脚本
    └── TASK_SPEC_执行层任务规格书.md
```

### 2.2 主仓库可提取脚本源（只读）
```
D:\Ai\Agent\xiangmu\xianyu_agent_workflow\src\
├── roles\product_maker\            # 网盘/发布/差异化/法律
├── roles\listing_optimizer\        # 上架/文案/质检
├── roles\marketing_planner\        # 文案生成/封面
├── roles\legal_guardian\           # 法律闸口
├── roles\competitor_analyzer\      # 差异化引擎
└── framework\scripts\              # 定时任务/预检/Cookie刷新
```

### 2.3 闲鱼运营配置（只读）
- Cookie 配置：`D:\Ai\xianyu-auto\config.yaml`（唯一真相，含 cookie2 + _tb_token_）
- 运营体系：`D:\Ai\xianyu-packages\游戏存档运营体系.md`（定价/节奏/限流铁律）
- 上架器：`D:\Ai\xianyu-packages\ops\` 现有脚本（list_live.py, fetch_all_metrics.py 等）

---

## 三、执行步骤（按顺序，逐条执行，异常即停）

### 步骤 1：环境就绪检查
**动作**：
1. 检查 Python 环境：`python --version`（需 3.10+）
2. 检查 bdpan CLI：`bdpan --version` 或 `bdpan whoami`
3. 检查 Cookie 有效性：`python D:\Ai\xianyu-packages\check_cookie.py`（退出码 0 = 可用）
4. 检查依赖包：`pip list | findstr "pyxianyu requests loguru pandas tqdm"`

**通过标准**：全部通过，无报错。

---

### 步骤 2：提取「Python 自动化办公脚本」源素材
**动作**：
1. 从主仓库 `src/roles/product_maker/`、`src/roles/listing_optimizer/`、`src/roles/marketing_planner/`、`src/framework/scripts/` 提取 **通用、可直接运行、无敏感信息** 的 `.py` 脚本
2. 筛选标准：
   - ✅ 通用工具类：Excel/Word/PDF/文件批量处理、爬虫/采集、定时任务、配置管理、日志/监控
   - ✅ 独立可运行：有 `if __name__ == "__main__":` 或明确入口
   - ✅ 依赖标准库/常见包：pandas, openpyxl, requests, loguru, tqdm 等
   - ❌ 排除：含硬编码 Cookie/密钥、含内部业务逻辑、测试脚本、一次性调试脚本
3. 目标数量：**20-30 个**高质量脚本
4. 放入：`D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\xianyu_virtual_resource_first_batch\yuan_daima\python_office_scripts\scripts\`（自建目录）

**产出**：
- `scripts/` 目录下 20-30 个 `.py` 文件
- `scripts/README.md`：脚本清单表（文件名 | 功能 | 入口 | 依赖 | 适用场景）

---

### 步骤 3：整理「素材加工自动化工具包」源素材
**动作**：
1. 已复制的核心文件（步骤 0 已完成）：
   - `differentiator.py` - 差异化加工引擎
   - `factory_publish.py` - 发布管线
   - `netdisk_bdpan.py` - 百度网盘通道
   - `netdisk_baidu.py` - 备用通道
   - `legal_gate.py` - 法律闸口
2. 需补充：
   - `differentiator.py` 的自检用例（文件末尾 `if __name__ == "__main__":` 部分）单独提取为 `demo_self_test.py`
   - 编写 `QUICKSTART.md`：5 分钟上手指南（安装依赖 → 跑自检 → 看输出）
   - 编写 `ARCHITECTURE.md`：四策略原理图解（整合、二次加工、优化、配套教程）
3. 目录结构：
```
material_processing_toolkit/
├── core/
│   ├── differentiator.py
│   ├── factory_publish.py
│   ├── netdisk_bdpan.py
│   ├── netdisk_baidu.py
│   └── legal_gate.py
├── demo/
│   ├── demo_self_test.py
│   └── sample_sources/          # 2-3 个演示用素材目录
├── QUICKSTART.md
├── ARCHITECTURE.md
└── requirements.txt             # 依赖列表
```

---

### 步骤 4：运行差异化加工（生成成品 ZIP）
**动作**：
对每个商品分别运行 `differentiator.py` 的主流程：

#### 商品 1：Python 自动化办公脚本合集
```bash
cd D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\xianyu_virtual_resource_first_batch\yuan_daima\python_office_scripts
python -c "
import sys, shutil
from pathlib import Path
sys.path.insert(0, r'D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\xianyu_virtual_resource_first_batch\yuan_daima\material_processing_toolkit')
from differentiator import Differentiator

# 源目录
src = Path(r'D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\xianyu_virtual_resource_first_batch\yuan_daima\python_office_scripts\scripts')
# 输出目录
out = Path(r'D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\xianyu_virtual_resource_first_batch\chengpin_shuchu')

d = Differentiator(out)
res = d.differentiate(
    [src],
    title='Python自动化办公脚本合集 50+实战案例',
    category='Python脚本',
    sources=[{'title': 'xianyu_agent_workflow 核心模块', 'source_url': 'https://github.com/...', 'author': 'Hermes Agent', 'license': 'MIT'}],
    license_key='MIT',
    obligations=['MIT 许可要求署名']
)
print(f'ZIP: {res.package_path}')
print(f'文件数: {res.stats[\"file_count\"]}')
print(f'大小: {res.stats[\"total_human\"]}')
"
```

#### 商品 2：素材加工自动化工具包
```bash
cd D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\xianyu_virtual_resource_first_batch\yuan_daima\material_processing_toolkit
python -c "
import sys
from pathlib import Path
sys.path.insert(0, '.')
from differentiator import Differentiator

src = Path('.')
out = Path(r'D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\xianyu_virtual_resource_first_batch\chengpin_shuchu')

d = Differentiator(out)
res = d.differentiate(
    [src],
    title='素材加工自动化工具包 差异化引擎+使用指南',
    category='开发工具',
    sources=[
        {'title': 'differentiator.py', 'source_url': 'https://github.com/...', 'author': 'Hermes Agent', 'license': 'MIT'},
        {'title': 'factory_publish.py', 'source_url': 'https://github.com/...', 'author': 'Hermes Agent', 'license': 'MIT'},
    ],
    license_key='MIT',
    obligations=['MIT 许可要求署名']
)
print(f'ZIP: {res.package_path}')
print(f'文件数: {res.stats[\"file_count\"]}')
print(f'大小: {res.stats[\"total_human\"]}')
"
```

**产出**（放入 `chengpin_shuchu/`）：
- `Python自动化办公脚本合集_50+实战案例.zip`
- `素材加工自动化工具包_差异化引擎+使用指南.zip`
- 每个 ZIP 内含：`00-内容总览.md`、`使用指南.md`、`ATTRIBUTION.txt`、`PROVENANCE.json`、分类目录文件

---

### 步骤 5：百度网盘上传 + 生成永久分享链接
**动作**：
使用 `factory_publish.py` 的 `BdpanNetdisk` 类，或直接用 bdpan CLI：

#### 方式 A：Python 代码（推荐，可复用发布管线）
```bash
cd D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\xianyu_virtual_resource_first_batch\yuan_daima\material_processing_toolkit
python -c "
import sys
from pathlib import Path
sys.path.insert(0, '.')
from netdisk_bdpan import BdpanNetdisk

nd = BdpanNetdisk(subdir='xianyu_resources', period=0)  # period=0 永久分享

# 上传商品 1
zip1 = Path(r'D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\xianyu_virtual_resource_first_batch\chengpin_shuchu\Python自动化办公脚本合集_50+实战案例.zip')
up1 = nd.upload_and_share(str(zip1), remote_dir='xianyu_resources')
print(f'商品1: {up1[\"link\"]} 提取码: {up1[\"pwd\"]}')

# 上传商品 2
zip2 = Path(r'D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\xianyu_virtual_resource_first_batch\chengpin_shuchu\素材加工自动化工具包_差异化引擎+使用指南.zip')
up2 = nd.upload_and_share(str(zip2), remote_dir='xianyu_resources')
print(f'商品2: {up2[\"link\"]} 提取码: {up2[\"pwd\"]}')
"
```

#### 方式 B：bdpan CLI 直跑（备用）
```bash
bdpan upload "D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\xianyu_virtual_resource_first_batch\chengpin_shuchu\Python自动化办公脚本合集_50+实战案例.zip" /apps/bdpan/xianyu_resources/
bdpan share /apps/bdpan/xianyu_resources/Python自动化办公脚本合集_50+实战案例.zip --period 0

bdpan upload "D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\xianyu_virtual_resource_first_batch\chengpin_shuchu\素材加工自动化工具包_差异化引擎+使用指南.zip" /apps/bdpan/xianyu_resources/
bdpan share /apps/bdpan/xianyu_resources/素材加工自动化工具包_差异化引擎+使用指南.zip --period 0
```

**产出**：记录到 `chengpin_shuchu\网盘链接表.txt`：
```
商品1 | Python自动化办公脚本合集 | https://pan.baidu.com/s/xxx | 提取码: xxxx
商品2 | 素材加工自动化工具包 | https://pan.baidu.com/s/yyy | 提取码: yyyy
```

**验收**：浏览器打开链接 + 提取码，能下载 ZIP，解压无损。

---

### 步骤 6：生成闲鱼商品文案（标题 + 描述 + 标签）
**动作**：
使用 `listing_copy.py` 的 `build_description` 生成合规文案。

#### 商品 1 参数
```python
pkg1 = {
    "title": "Python自动化办公脚本合集 50+实战案例",
    "category": "Python脚本",
    "items": ["内容总览", "使用指南", "50+ 个脚本文件", "授权说明 ATTRIBUTION.txt", "加工留痕 PROVENANCE.json"],
    "stats": {"file_count": 50, "source_count": 1},
    "license_key": "MIT",
    "delivery": {"file_count": 50, "netdisk_url": "<步骤5得到的链接>", "netdisk_pwd": "<提取码>"},
    "deliver_mode": "百度网盘永久链接 + 提取码"
}
diff1 = {
    "strategies": [
        "把 50+ 个分散脚本整合成统一目录结构，按功能分类",
        "逐个查重，剔除重复文件，不占空间",
        "附一份内容清单，想找哪个脚本一眼定位",
        "附一份使用指南，拿到手知道怎么用、怎么改、先跑哪个"
    ]
}
```

#### 商品 2 参数
```python
pkg2 = {
    "title": "素材加工自动化工具包 差异化引擎+使用指南",
    "category": "开发工具",
    "items": ["核心引擎 4 个模块", "演示自检用例", "快速上手指南", "架构原理文档", "授权说明", "加工留痕"],
    "stats": {"file_count": 10, "source_count": 1},
    "license_key": "MIT",
    "delivery": {"file_count": 10, "netdisk_url": "<步骤5得到的链接>", "netdisk_pwd": "<提取码>"},
    "deliver_mode": "百度网盘永久链接 + 提取码"
}
diff2 = {
    "strategies": [
        "四策略全自动：整合去重、统一目录、生成总览、原创教程",
        "输入素材目录 → 一键出标准化成品包",
        "自带法律闸口、授权留痕、合规自检",
        "附完整源码+文档，可直接二次开发或集成进你的流水线"
    ]
}
```

**执行命令**：
```bash
cd D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\xianyu_virtual_resource_first_batch\yuan_daima\python_office_scripts
python -c "
import sys
sys.path.insert(0, '.')
from listing_copy import build_description, validate_no_false_claims

pkg1 = {...}  # 上面的参数
diff1 = {...}
desc1 = build_description(pkg1, diff1)
print('=== 商品1 描述 ===')
print(desc1)
print('合规检查:', validate_no_false_claims(desc1, pkg1) or '✅ 通过')

pkg2 = {...}
diff2 = {...}
desc2 = build_description(pkg2, diff2)
print('=== 商品2 描述 ===')
print(desc2)
print('合规检查:', validate_no_false_claims(desc2, pkg2) or '✅ 通过')
"
```

**产出**：保存到 `ops\商品文案_商品1.txt`、`ops\商品文案_商品2.txt`

---

### 步骤 7：生成封面图（750×1000 JPEG）
**动作**：
使用 `cover_designer.py` 或简单脚本生成。最低要求：
- 尺寸：750×1000
- 内容：商品标题（前 20 字）+ 核心卖点 3 条 + 「百度网盘永久链接 · 秒发」+ 价格标签
- 格式：JPEG，质量 90+

**简易生成命令**（若无 cover_designer 可用）：
```bash
cd D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\xianyu_virtual_resource_first_batch\ops
python -c "
from PIL import Image, ImageDraw, ImageFont
import textwrap

def make_cover(title, price, bullets, out_path):
    img = Image.new('RGB', (750, 1000), color='#1a1a2e')
    draw = ImageDraw.Draw(img)
    # 标题
    try:
        font_title = ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 48)
        font_body = ImageFont.truetype('C:/Windows/Fonts/msyh.ttc', 32)
    except:
        font_title = ImageFont.load_default()
        font_body = ImageFont.load_default()
    
    # 标题区
    y = 80
    for line in textwrap.wrap(title, width=14):
        draw.text((50, y), line, fill='#ffffff', font=font_title)
        y += 60
    
    # 价格
    draw.text((50, y+20), f'¥{price}', fill='#ffd700', font=ImageFont.truetype('C:/Windows/Fonts/msyhbd.ttc', 56))
    
    # 卖点
    y += 100
    for i, b in enumerate(bullets, 1):
        draw.text((80, y), f'{i}. {b}', fill='#e0e0e0', font=font_body)
        y += 50
    
    # 底部
    draw.text((50, 900), '百度网盘永久链接 · 拍下秒发 · 无远程服务', fill='#888888', font=font_body)
    
    img.save(out_path, 'JPEG', quality=95)
    print(f'封面已生成: {out_path}')

make_cover('Python自动化办公脚本合集\n50+实战案例', '2.9', 
    ['50+ 可直接跑的办公脚本', 'Excel/Word/PDF/文件批量全覆盖', '附使用指南+内容清单，下载即用'],
    r'D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\xianyu_virtual_resource_first_batch\chengpin_shuchu\cover_商品1.jpg')

make_cover('素材加工自动化工具包\n差异化引擎+使用指南', '3.9',
    ['四策略全自动：整合/加工/优化/教程', '源码级交付，可直接二次开发集成', '自带法律闸口+合规自检，用得放心'],
    r'D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\xianyu_virtual_resource_first_batch\chengpin_shuchu\cover_商品2.jpg')
"
```

**产出**：`chengpin_shuchu\cover_商品1.jpg`、`cover_商品2.jpg`

---

### 步骤 8：闲鱼上架（使用现有上架器或 phase3_lister）
**动作**：
优先用 `D:\Ai\xianyu-packages\ops\` 下的现有发布流程，或改造 `phase3_lister.py`。

#### 关键参数
| 字段 | 商品 1 | 商品 2 |
|------|--------|--------|
| 标题 | Python自动化办公脚本合集 50+实战案例 | 素材加工自动化工具包 差异化引擎+使用指南 |
| 价格 | 2.9 | 3.9 |
| 类目 | 电脑软件/虚拟物品/源码/脚本 | 电脑软件/虚拟物品/开发工具 |
| 图片 | cover_商品1.jpg | cover_商品2.jpg |
| 描述 | 步骤 6 生成的文案 | 步骤 6 生成的文案 |
| 发货方式 | 自动发货（网盘链接+提取码） | 自动发货（网盘链接+提取码） |
| 库存 | 9999 | 9999 |
| 标签 | Python,自动化办公,脚本,Excel,爬虫 | Python,自动化工具,差异化,素材加工 |

**执行**：
```bash
# 方案 A：用现有 xianyu-packages 发布脚本（如有）
cd D:\Ai\xianyu-packages
# 检查是否有 publish_item.py 或类似脚本
dir ops\

# 方案 B：用 phase3_lister.py（需适配）
cd D:\Ai\Agent\gongzuoqu\03_xiangmu_geli_wenjianjia\xianyu_virtual_resource_first_batch\yuan_daima\python_office_scripts
python -c "
# 这里需要根据 phase3_lister.py 的实际接口调用
# 先读源码确认 ListingTask 结构和 publish 方法
"
```

**若现有工具链不直接可用**，最小可行性：手工在闲鱼网页端上架 2 条（复制粘贴标题/描述/上传封面/填价格/填网盘链接），记录 item_id。

**产出**：记录到 `ops\上架记录.txt`：
```
商品1 | item_id: 109xxxxxxxxxx | 标题: Python自动化办公脚本合集... | 价格: 2.9 | 状态: 在售
商品2 | item_id: 109xxxxxxxxxx | 标题: 素材加工自动化工具包... | 价格: 3.9 | 状态: 在售
```

---

### 步骤 9：首单破零 + 基线数据记录
**动作**：
1. 找 2-3 个朋友/小号真拍真评（每人买 1 条不同商品）
2. 走完：拍下 → 私聊 → 发链接 → 确认可用 → 好评
3. 跑基线数据：
```bash
python D:\Ai\xianyu-packages\check_cookie.py
cd D:\Ai\xianyu-packages\ops
$env:PYTHONIOENCODING='utf-8'
python fetch_all_metrics.py   # 记录浏览/想要/收藏/私聊
python list_live.py           # 确认在售条数
```

**产出**：`ops\首周基线数据.txt`
```
日期: 2026-11-x
商品1 | 浏览: x | 想要: x | 收藏: x | 私聊: x | 成交: 1 | 好评: 1
商品2 | 浏览: x | 想要: x | 收藏: x | 私聊: x | 成交: 1 | 好评: 1
```

---

### 步骤 10：输出执行总结
**动作**：生成 `ops\EXECUTION_SUMMARY.md`：
```markdown
# 执行总结：首批虚拟资源上架

## 完成情况
- [ ] 步骤1 环境检查
- [ ] 步骤2 提取 Python 脚本 (N 个)
- [ ] 步骤3 整理工具包素材
- [ ] 步骤4 差异化加工生成 2 个 ZIP
- [ ] 步骤5 百度网盘上传+分享链接
- [ ] 步骤6 生成合规文案
- [ ] 步骤7 生成封面图
- [ ] 步骤8 闲鱼上架 (item_id: xxx, yyy)
- [ ] 步骤9 首单破零 + 基线数据

## 关键产出
| 商品 | ZIP路径 | 网盘链接 | 提取码 | 闲鱼item_id | 价格 |
|------|---------|----------|--------|-------------|------|
| Python脚本合集 | ... | ... | ... | ... | 2.9 |
| 素材加工工具包 | ... | ... | ... | ... | 3.9 |

## 遇到的问题及解决
- 问题1：...
- 问题2：...

## 下一步建议
- 扩充至 5 条：增加 音效包 / 字体包 / AI部署包
- 接入夸克网盘双盘发货
- 建立每日巡检自动化
```

---

## 四、异常处理规范

| 异常场景 | 处理动作 |
|----------|----------|
| `check_cookie.py` 退出码非 0 | **停止**，上报：【Cookie 失效，需用户手工更新】 |
| `bdpan` 未安装/未登录 | **停止**，上报：【需安装 bdpan CLI 并完成 OAuth 授权】 |
| 差异化加工报错（如无素材） | **停止**，上报：【源素材目录为空或结构异常】 |
| 网盘上传失败（配额/限速） | 重试 3 次（间隔 60s），仍失败则上报 |
| 闲鱼上架报错（限流/审核） | 记录错误码，间隔 115s 重试 1 次，失败上报 |
| 合规自检不通过 | **禁止上架**，修正文案后重跑步骤 6 |

---

## 五、禁止事项（红线）

1. **不得**修改 `legal_gate.py` 的许可判定逻辑（默认拒绝 NC/ND/UNKNOWN）
2. **不得**上传未跑过 `legal_gate.check_resource()` 的素材
3. **不得**编造文案数字（必须通过 `validate_no_false_claims`）
4. **不得**使用除百度网盘外的网盘（按决策层指令）
5. **不得**设置远程服务/安装指导类 SKU（纯网盘包）
6. **不得**修改 `factory_publish.py` 的注册表复用机制（防分享配额耗尽）

---

## 六、验收清单（全部 ✅ 才算任务完成）

- [ ] 步骤 1 环境检查通过
- [ ] 步骤 2 提取 20-30 个 Python 脚本，README 完整
- [ ] 步骤 3 工具包目录结构完整，含 QUICKSTART/ARCHITECTURE
- [ ] 步骤 4 两个 ZIP 生成成功，内含 4 大件（总览/指南/授权/留痕）
- [ ] 步骤 5 两个永久分享链接可打开、可下载、解压无损
- [ ] 步骤 6 文案通过合规自检，无编造数字/违禁词
- [ ] 步骤 7 两张封面 750×1000 JPEG 生成成功
- [ ] 步骤 8 两条商品在闲鱼上架成功，item_id 记录在案
- [ ] 步骤 9 首单破零（≥1 真实成交/好评），基线数据记录
- [ ] 步骤 10 `EXECUTION_SUMMARY.md` 落盘

---

## 七、汇报格式（每步骤完成后输出）

```
【当前步骤】步骤 N：<步骤名>
【执行动作】<具体执行的命令/操作>
【结果/返回数据】<关键输出：文件路径、链接、item_id、错误信息等>
【状态】完成 / 待补充 / 异常终止
```

---

> **执行层只负责按此规格书逐步执行**。任何缺失参数、模糊指令、超出权限的决策，直接按 SOUL.md 规则上报：【待补充】或【需要规划层决策】。