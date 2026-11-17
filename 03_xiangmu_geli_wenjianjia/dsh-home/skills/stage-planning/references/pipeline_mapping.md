# 流水线阶段映射表 — novel_pipeline 三阶段知识加载指南

> 供 `run_pipeline.py` 按阶段加载，注入到 LLM system prompt。
> 所有知识点引用 `writing_robert_mckee_story` 章节/附件，保持单一真相源。

---

## 阶段定义（与 InkOS 管线对齐）

| pipeline 阶段 | 对应 mapping key | 触发节点 | 核心任务 |
|---------------|------------------|----------|----------|
| **Planning** | `planning` | `scan_bangdan` → `deconstruct_novel` → `generate_outline` | 搭骨架、定脊柱、锁类型、设反派、三幕打桩 |
| **Writing** | `writing` | `inkos write next` / `inkos draft` | 逐场生成：价值翻转、节拍精细、潜台词承载 |
| **Review** | `review` | `quality_check` / `human_review` / `lower_ai` | 宏观→中观→微观→主题四层诊断，硬指标不通过即返工 |

---

## 1. Planning 阶段知识包

### 必加载文件
```
writing_robert_mckee_story/
├── ch02-structure-spectrum.md   # 结构谱系选型
├── ch03-setting.md              # 背景四维锁死
├── ch06-meaning.md              # 控制性思想定稿
├── ch07-substance.md            # 故事脊柱画图
├── ch08-inciting.md             # 激励事件+MDQ
├── ch09-act-design.md           # 三幕打桩+不归点链
├── ch14-antagonism.md           # 反派四层级+否定之否定
├── ch17-character.md            # 人物弧光三阶段
├── references/confusion_watch.md # 概念隔离（防幻觉）
├── patterns.md#1,2,4,5,6        # 模板：激励事件/三幕/反派/弧光/控制性思想
└── cheatsheet.md#precheck,decision_rules # 写作前自检+核心决策规则
```

### 注入到 System Prompt 的精简版
```markdown
# PLANNING STAGE KNOWLEDGE (注入版)

## 结构谱系锁定 [Ch2]
- 必选：Archplot/Miniplot/Antiplot 其一
- Archplot=单一主角+因果闭环+三幕线性+封闭结局+外在冲突主导

## 背景四维锁死 [Ch3]
- 时代/期限/地点/冲突层面 — 全锁死，世界越小创作选择越多

## 控制性思想定稿 [Ch6]
- 格式："价值 + 原因" (如：正义胜出，因为正直者敢于牺牲)
- 所有场景/角色/对白必须服务或反讽此命题

## 故事脊柱 [Ch7]
- 欲望 → 反派力量 → 行动 → 结果 (因果链闭环)
- Gap(缺口)=期望与结果差距=故事能量源

## 激励事件 [Ch8]
- 必须在银幕上、不可逆、创造MDQ("主角能否...")
- 四类型：决定/意外/大事件/安静内在事件

## 三幕打桩 [Ch9]
- PP1(25%)：主角主动选择进入第二幕
- Midpoint(50%)：价值首次大逆转，赌注升级
- PP2(75%)：危机前夜，最艰难抉择
- 进展=不归点链：每越过一个不归点，排除该力度行动

## 反派力量 [Ch14]
- 四层级量身定制：社会/制度 → 个人/人际 → 内在/心理 → 环境/命运
- 价值负面进展：正面 → 相反价值 → 矛盾价值 → **否定之否定(专制/自厌/自欺)**

## 人物弧光 [Ch17]
- 面具期(一幕) → 剥离期(二幕) → 真实期(三幕)
- 核心矛盾=欲望 vs 恐惧，压力下选择揭示真相

## 概念隔离红线 [confusion_watch.md]
- 激励事件≠PP1；危机≠高潮；反派力量≠反面角色；矛盾价值≠否定之否定
- 控制性思想≠主题≠前提；潜台词≠隐性；幕后故事≠说明
```

### 可用模板（直接填充）
- `patterns.md#1` 激励事件设计模板
- `patterns.md#2` 三幕结构打桩表
- `patterns.md#4` 反派力量设计表
- `patterns.md#5` 人物弧光设计表
- `patterns.md#6` 控制性思想验证清单

### 自检清单（输出前必过）
- `cheatsheet.md`「写作前自检」7项全部 ✅
- 脊柱闭环？控制性思想句式？结构类型？背景四维？激励事件银幕上？MDQ清楚？三幕打桩全？

---

## 2. Writing 阶段知识包

### 必加载文件
```
writing_robert_mckee_story/
├── ch10-scene-design.md         # 场景五步法
├── ch11-scene-analysis.md       # 节拍/文本vs潜文本
├── ch12-composition.md          # 进度/节奏/速度
├── ch15-exposition.md           # 说明=弹药
├── ch18-text.md                 # 潜台词三层/对白铁律
├── references/confusion_watch.md # 概念隔离
├── patterns.md#3,7,8,9         # 模板：场景卡片/说明检查/价值逆转/对白质量
└── cheatsheet.md#quick_check,decision_rules_writing # 场景自检+写作期决策规则
```

### 注入到 System Prompt 的精简版
```markdown
# WRITING STAGE KNOWLEDGE (注入版)

## 场景设计五步法 [Ch10]
1. 确定场景价值(什么在赌注上)
2. 追踪节拍(每个 Action/Reaction)
3. 识别转折点(价值何时逆转)
4. 评估情感充电(正/负，电量/10)
5. 验证推进脊柱/MDQ

## 节拍 = 动作/反应 [Ch2, Ch11]
- 最小单位，带情感色彩的进行时短语："正在恳求"、"正在对其恳求置之不理"
- 场景=节拍累积→价值翻转

## 文本 vs 潜文本 [Ch11]
- 文本=感官表面(对白/动作/声音)
- 潜文本=被隐藏的思想情感/冲动/伊德(70%)
- **铁律**：场景若讲它表面讲的东西 = 掉进粪坑
- 换轮胎法：表面谈A(轮胎)，潜文本谈B(关系)

## 潜台词三层 [Ch18]
- 显性(说出/10%) < 隐性(有意隐藏/20%) < 潜台词(真实/潜意识/70%)
- 四步写法：写显性 → 挖隐性 → 挖潜台词 → 重写对白让显性承载潜台词

## 说明/铺垫 [Ch15]
- 三原则：作为弹药/展示非讲述/必要性最小化
- 禁忌：旁白大段/"如你所知"/信息倾倒
- 进度：最不重要最先，秘密留最后
- 幕后故事留到危机/高潮揭示转折

## 对白铁律 [Ch18]
- 压缩简约/方向性/目的性/结构简单/悬念句/无言优先
- 言如常人，思若智者

## 进度/节奏/速度 [Ch12]
- 进度：紧张→松弛→更高紧张→更深松弛→顶峰(像性/长跑)
- 节奏：场景长度变化(1分↔4分，30秒↔6分)，高潮前挣得停顿资格
- 速度：对白/动作密度，奔向高潮时螺旋提升

## 概念隔离红线 [confusion_watch.md]
- 场景无价值逆转=填充材料(必删)
- 潜台词≠隐性(撒谎)；幕后故事≠说明(早倾倒)
- 文本谈A，潜文本谈B；无"写在鼻子上"对白
```

### 可用模板（每场景一张卡片）
- `patterns.md#3` 场景设计卡片（价值/冲突层级/节拍追踪/转折点/充电/推进脊柱/潜台词核心）
- `patterns.md#7` 说明/铺垫植入检查
- `patterns.md#8` 场景价值逆转自检（开始/结束价值必须相反、转折点节拍、潜台词承载、推进脊柱）
- `patterns.md#9` 对白质量检查（压缩/方向/目的/简单/悬念句/无言优先/潜台词密度/无写在鼻子上）

### 场景级自检（每场生成后必过）
- `cheatsheet.md`「快速自检表」10项：
  - [ ] 价值正负翻转？ [ ] 推进脊柱/MDQ？ [ ] 冲突层级升级？ [ ] 反派针对弱点？ [ ] 潜台词承载真意？ [ ] 说明作弹药？ [ ] 客观对应物替代形容词？ [ ] 无被动/无形容词堆砌/无头跳？ [ ] 伏笔分晓闭合？ [ ] 四重效果触发？

---

## 3. Review 阶段知识包

### 必加载文件
```
writing_robert_mckee_story/
├── ch06-meaning.md              # 控制性思想验证
├── ch09-act-design.md           # 幕/序列/场景节奏
├── ch10-scene-design.md         # 场景价值翻转
├── ch11-scene-analysis.md       # 潜文本/节拍分析
├── ch12-composition.md          # 社会/个人/象征/反讽进展
├── ch13-crisis-climax.md        # 危机/高潮/结局三位一体
├── ch14-antagonism.md           # 反派否定之否定
├── ch15-exposition.md           # 说明植入
├── ch16-problems.md             # 八大常见问题
├── ch18-text.md                 # 潜台词/描写/形象系统
├── references/confusion_watch.md
├── patterns.md#6,8              # 控制性思想验证/场景价值逆转自检
├── cheatsheet.md#rewrite_order,tells_smells # 修改顺序+症状诊断
└── cheatsheet.md#hard_gates     # 硬性通过线
```

### 注入到 System Prompt 的精简版
```markdown
# REVIEW STAGE KNOWLEDGE (注入版)

## 四层修改顺序（严禁跳步） [Ch19]
1. **宏观**：脊柱闭环？人物弧光完整？控制性思想高潮验证？结构类型匹配？反派否定之否定达成？
2. **中观(幕/序列/场景)**：每幕高潮逆转？序列递增？场景价值翻转？节奏递快？进度螺旋升降？
3. **微观**：对白潜台词？展示非讲述？客观对应物？说明植入？悬念句？无言优先？
4. **主题**：问"在说什么" → 删不服务/强服务/植入象征

## 硬性通过线（自动化断言）
| 指标 | 通过标准 | 失败即返工 |
|------|----------|------------|
| 场景价值翻转率 | 100% (无例外) | ✅/❌ |
| 脊柱闭环 | 是/否 | ✅/❌ |
| 控制性思想高潮验证 | 是/否 | ✅/❌ |
| 反派否定之否定达成 | 是/否 (专制/自厌/自欺) | ✅/❌ |
| 潜台词密度抽检 | ≥3/5 场景可辨人设/真意 | ✅/❌ |
| 无"写在鼻子上"对白 | 0 处 | ✅/❌ |
| 无头跳/被动主角/巧合解决 | 0 处 | ✅/❌ |

## 症状→诊断→处方 (Tells & Smells) [Ch16]
| 症状 | 诊断 | 处方 |
|------|------|------|
| "他很生气/房间很乱" | 讲述成瘾 | 强制展现(可拍摄动作) |
| 旁白大段交代 | 说明过度 | 转环境叙事/弹药植入 |
| "如你所知"对白 | 假对白 | 冲突中自然说出 |
| 人物像功能符号 | 缺维度 | 补矛盾/一致性/复杂性(维=矛盾) |
| 情节像流水账 | 缺因果链 | 画脊柱图：欲望→反派→行动→结果 |
| 主题生硬/说教 | 硬贴标签 | 完稿问"在说什么"回头强化 |
| 场景无价值逆转 | 填充材料 | 删或重写，必须正负翻转 |
| 冲突层级不升级 | 平铺直叙 | 社会→个人→内在层层升级 |
| 反派不针对弱点 | 威胁不足 | 重设反派：精准打击主角恐惧 |
| 激励事件 off-screen | 作弊 | 移到银幕上 |
| 危机不是抉择 | 困境≠危机 | 改成两难抉择(两善/两恶之轻) |
| 高潮可逆/非主角 | 无效高潮 | 重写：主角驱动、不可逆、纯粹清白 |
| 视角在头里跳 | 头跳(大忌) | 定视角、标记跳跃 |
| 对白华丽/文学 | 注意力在语言 | 删掉，言如常人思若智者 |

## 概念隔离红线 [confusion_watch.md]
- 危机=静态抉择，高潮=动态逆转，结局=新稳态（三位一体不混淆）
- 反派力量=系统四层级，非单一反面角色
- 否定之否定=双重负面质变(专制/自厌/自欺)，非单纯犯罪/恨
- 控制性思想=价值+原因闭合句，非抽象主题
- 潜台词=角色自己不知的真实(70%)，非有意隐藏的撒谎(隐性)
- 幕后故事=留到高潮的转折弹药，非早早倾倒的说明
```

### 自动化质检脚本接口（Python 伪代码）
```python
# quality_check.py 接入示例
def hard_gates_assert(chapters_dir: Path, book_id: str) -> tuple[bool, list[str]]:
    """返回 (通过否, 失败详情列表)"""
    failures = []
    
    # 1. 场景价值翻转率 100%
    for ch_file in sorted(chapters_dir.glob("*.txt")):
        scene = parse_scene(ch_file)
        if scene.start_value == scene.end_value:
            failures.append(f"{ch_file.name}: 场景价值未翻转 ({scene.start_value}→{scene.end_value})")
    
    # 2. 脊柱闭环
    if not verify_spine_closure(book_id):
        failures.append("脊柱未闭环：欲望→反派力量→行动→结果 因果断裂")
    
    # 3. 控制性思想高潮验证
    if not verify_controlling_idea_at_climax(book_id):
        failures.append("高潮未验证控制性思想")
    
    # 4. 反派否定之否定
    if not verify_negation_of_negation(book_id):
        failures.append("反派未达否定之否定(专制/自厌/自欺)")
    
    # 5. 潜台词密度抽检
    sampled = random.sample(list(chapters_dir.glob("*.txt")), min(5, total))
    passed = sum(1 for f in sampled if subtext_density_pass(f))  # 遮人名辨人设+辨真意
    if passed < 3:
        failures.append(f"潜台词密度不足：{passed}/5 通过")
    
    # 6. 禁忌扫描
    for ch_file in chapters_dir.glob("*.txt"):
        text = ch_file.read_text()
        if re.search(r"(如你所知|正如你所知|大家都知道)", text):
            failures.append(f"{ch_file.name}: 含'如你所知'假对白")
        if has_head_hopping(text):
            failures.append(f"{ch_file.name}: 视角头跳")
        if has_passive_protagonist(text):
            failures.append(f"{ch_file.name}: 被动主角")
    
    return len(failures) == 0, failures
```

---

## 调用约定（给 run_pipeline.py 用）

```python
# run_pipeline.py 集成示例
from pathlib import Path

SKILL_BASE = Path("/home/user01/.hermes/skills/writing_robert_mckee_story")

def load_stage_knowledge(stage: str) -> str:
    """按阶段加载知识片段，返回合并后的 markdown 字符串"""
    parts = []
    
    if stage == "planning":
        # 核心章节
        for ch in ["ch02", "ch03", "ch06", "ch07", "ch08", "ch09", "ch14", "ch17"]:
            parts.append((SKILL_BASE / "chapters" / f"{ch}-*.md").read_text())
        # 附件
        parts.append((SKILL_BASE / "references" / "confusion_watch.md").read_text())
        # 模板片段
        parts.append(extract_section(SKILL_BASE / "patterns.md", ["1", "2", "4", "5", "6"]))
        # 自检
        parts.append(extract_section(SKILL_BASE / "cheatsheet.md", ["precheck", "decision_rules"]))
    
    elif stage == "writing":
        for ch in ["ch10", "ch11", "ch12", "ch15", "ch18"]:
            parts.append((SKILL_BASE / "chapters" / f"{ch}-*.md").read_text())
        parts.append((SKILL_BASE / "references" / "confusion_watch.md").read_text())
        parts.append(extract_section(SKILL_BASE / "patterns.md", ["3", "7", "8", "9"]))
        parts.append(extract_section(SKILL_BASE / "cheatsheet.md", ["quick_check", "decision_rules_writing"]))
    
    elif stage == "review":
        for ch in ["ch06", "ch09", "ch10", "ch11", "ch12", "ch13", "ch14", "ch15", "ch16", "ch18"]:
            parts.append((SKILL_BASE / "chapters" / f"{ch}-*.md").read_text())
        parts.append((SKILL_BASE / "references" / "confusion_watch.md").read_text())
        parts.append(extract_section(SKILL_BASE / "patterns.md", ["6", "8"]))
        parts.append(extract_section(SKILL_BASE / "cheatsheet.md", ["rewrite_order", "tells_smells", "hard_gates"]))
    
    return "\n\n---\n\n".join(parts)

def extract_section(filepath: Path, section_ids: list[str]) -> str:
    """从 patterns.md/cheatsheet.md 提取指定编号的模板/清单"""
    # 实现：按 ## 数字. 标题 分割，返回匹配 id 的块
    pass

# 在各阶段调用前注入：
# planning 阶段
system_prompt += "\n\n" + load_stage_knowledge("planning")

# writing 阶段 (每次 inkos write next 前)
system_prompt += "\n\n" + load_stage_knowledge("writing")

# review 阶段 (quality_check 前)
system_prompt += "\n\n" + load_stage_knowledge("review")
```

---

## 版本控制建议

| 文件 | 变更频率 | 策略 |
|------|----------|------|
| `chapters/ch01-ch19.md` | **极低** | 只读，只增，带原文行号，不重写 |
| `glossary.md/patterns.md/cheatsheet.md` | 低 | 小幅补全，保持向后兼容 |
| `references/confusion_watch.md` | 中 | 发现新易混对即追加，版本号递增 |
| `references/pipeline_mapping.md` | 中 | pipeline 阶段调整时同步更新 |
| `run_pipeline.py` 注入逻辑 | 高 | 代码版本控制，与 mapping.md 联动 |

---

## 维护检查清单（每次 pipeline 迭代后）

- [ ] `confusion_watch.md` 是否覆盖了本次迭代遇到的新幻觉类型？
- [ ] `pipeline_mapping.md` 的阶段映射是否与 `run_pipeline.py` 实际阶段名一致？
- [ ] 硬性通过线断言是否在 `quality_check.py` 中真正执行？
- [ ] 注入 token 数是否在可接受范围（建议 < 8k tokens/阶段）？
- [ ] 是否有章节文件被误改？（git diff 检查 chapters/ 目录）

---

*最后更新: 2026-10-07*
*基于 novel_pipeline v1.1.0 架构对齐，随 pipeline 迭代同步维护*