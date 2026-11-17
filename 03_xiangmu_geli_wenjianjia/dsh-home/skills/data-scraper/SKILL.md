---
name: data-scraper
description: 数据清洗师：多源数据采集/清洗/结构化/存储，输出可直接分析的高质量数据集
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [data, scraping, cleaning, etl, pipeline, dataset, revenue]
    related_skills: [seo-auditor, content-writer, lead-generator, competitor-analyzer]
    requires_toolsets: [terminal, web, file, web_search]
---

# 数据清洗师

**核心使命**：多源数据采集、清洗、结构化、存储，输出**可直接分析的高质量数据集**，零 Token 成本。

---

## 🎯 适用场景

| 触发条件 | 产出物 |
|----------|--------|
| 客户需要 "数据采集/清洗/结构化" | 标准化数据集 + ETL 管道 |
| 竞品/市场数据采集 | 结构化数据集 + 更新管道 |
| 线索/客户数据清洗 | 去重/标准化/画像后的干净数据 |
| 训练数据准备 | 标注就绪的训练/测试集 |
| 定期数据监控 | 定时更新的数据看板 |

---

## 🔄 标准 ETL 流程

```python
def run_etl_pipeline(source_config: dict, transform_rules: dict, sink_config: dict) -> dict:
    """
    标准 ETL 管道
    :param source_config: 数据源配置
    :param transform_rules: 转换规则
    :param sink_config: 目标存储配置
    :return: 执行报告
    """
    # 1. Extract: 多源并行采集
    raw_data = parallel_extract(source_config)
    
    # 2. Transform: 并行清洗/转换
    clean_data = parallel_transform(raw_data, transform_rules)
    
    # 3. Load: 写入目标存储
    load_result = load_to_sink(clean_data, sink_config)
    
    # 4. Validate: 数据质量校验
    quality_report = validate_quality(clean_data)
    
    return {
        "records_processed": len(clean_data),
        "quality_score": quality_report.score,
        "output_path": sink_config["path"],
        "quality_report": quality_report
    }
```

---

## 🔍 采集矩阵

| 数据源 | 采集方式 | 适用场景 | 工具 | 频率 |
|--------|----------|----------|------|------|
| **Web 页面** | `browser_exec` (Playwright) + `terminal` (curl/wget) | 动态/静态页面 | Playwright/Selenium/curl | 实时/定时 |
| **API** | `terminal` (curl/HTTPie) + `web_search` | REST/GraphQL/RSS | curl/HTTPie/GraphQL Client | 实时/轮询 |
| **文件** | `terminal` (aws s3 cp/gsutil/rsync) | CSV/JSON/Parquet/Excel | pandas/polars/awscli | 批量/增量 |
| **数据库** | `terminal` (pg_dump/mysqldump/sqlite3) | PostgreSQL/MySQL/SQLite | pg_dump/pgloader | 定时/增量 |
| **文档** | `browser_exec` (PDF/Word/HTML 解析) | PDF/Word/HTML/Notion | pdfplumber/python-docx | 批量 |
| **社交/论坛** | `web_search` + `browser_exec` | Reddit/Twitter/Discord/知乎 | PRAW/tweepy/Playwright | 定时 |
| **代码仓库** | `terminal` (git clone/GitHub API) | GitHub/GitLab/Gitea | PyGithub/GitLab API | 定时 |

---

## 🧹 清洗标准化流程

```python
def standard_cleaning_pipeline(df: pd.DataFrame, rules: dict) -> pd.DataFrame:
    """标准清洗管道"""
    # 1. 列名标准化
    df.columns = [standardize_column_name(c) for c in df.columns]
    
    # 2. 类型推断与转换
    df = infer_and_cast_types(df, rules.get("type_hints", {}))
    
    # 3. 缺失值处理
    df = handle_missing_values(df, rules.get("missing", "drop"))
    
    # 3. 去重
    df = deduplicate(df, rules.get("dedup_keys", []))
    
    # 4. 异常值处理
    df = handle_outliers(df, rules.get("outliers", "iqr"))
    
    # 5. 格式标准化
    df = standardize_formats(df, rules.get("formats", {}))
    
    # 6. 衍生特征
    df = derive_features(df, rules.get("derived", []))
    
    return df
```

### 清洗规则配置示例
```yaml
transform_rules:
  type_hints:
    price: float
    date: datetime
    email: string
    phone: string
    url: string
  missing:
    strategy: "fill"  # drop/fill/interpolate
    fill_values:
      price: 0
      category: "unknown"
  dedup_keys: ["id", "email", "url"]
  outliers:
    method: "iqr"  # iqr/zscore/isolation_forest
    columns: ["price", "quantity"]
  formats:
    date: "%Y-%m-%d"
    phone: "E.164"
    email: "lowercase"
    url: "normalize"
  derived:
    - name: "price_per_unit"
      formula: "price / quantity"
    - name: "days_since_created"
      formula: "(today - created_date).days"
```

---

## 📦 数据质量验证

```python
def validate_quality(df: pd.DataFrame, rules: dict) -> QualityReport:
    """数据质量验证"""
    report = QualityReport()
    
    # 1. 完整性
    report.completeness = 1 - df.isnull().sum().sum() / (df.shape[0] * df.shape[1])
    
    # 2. 唯一性
    report.uniqueness = 1 - df.duplicated().sum() / len(df)
    
    # 3. 一致性
    report.consistency = check_consistency(df, rules.get("constraints", []))
    
    # 4. 有效性
    report.validity = check_validity(df, rules.get("validations", {}))
    
    # 5. 准确性（抽样人工复核）
    report.accuracy = sample_accuracy_check(df)
    
    # 6. 及时性
    report.timeliness = check_freshness(df, rules.get("max_age_days", 30))
    
    report.score = (report.completeness + report.uniqueness + 
                   report.consistency + report.validity + 
                   report.accuracy + report.timeliness) / 6
    return report
```

### 质量阈值
| 指标 | 优秀 | 合格 | 预警 |
|------|------|------|------|
| 完整性 | ≥ 99% | ≥ 95% | < 90% |
| 唯一性 | 100% | ≥ 99% | < 95% |
| 一致性 | 100% | ≥ 99% | < 95% |
| 有效性 | 100% | ≥ 99% | < 95% |
| 综合评分 | ≥ 95 | ≥ 90 | < 85 |

---

## 📦 标准输出格式

```
dataset-package/
├── data/
│   ├── dataset.parquet         # 主数据 (列式存储，高效)
│   ├── dataset.csv             # CSV 备选
│   └── dataset.jsonl           # JSONL (流式处理)
├── schema/
│   ├── schema.json             # JSON Schema
│   ├── schema.sql              # SQL DDL
│   └── schema.yaml             # YAML Schema
├── quality/
│   ├── quality_report.json     # 质量报告
│   ├── profile_report.html     # ydata-profiling 报告
│   └── sample_validation.csv   # 抽样验证记录
├── docs/
│   ├── README.md               # 数据集说明
│   ├── data_dictionary.md      # 数据字典
│   ├── lineage.md              # 数据血缘
│   └── changelog.md            # 变更日志
├── scripts/
│   ├── load.py                 # 加载脚本
│   ├── validate.py             # 验证脚本
│   └── update.py               # 增量更新脚本
└── metadata.json               # 元数据
```

---

## 📊 变现指标

| 指标 | 目标值 |
|------|--------|
| 单价 | $100-2000/数据集 |
| 交付周期 | 2-24 小时 |
| 数据质量评分 | ≥ 95/100 |
| 客户满意度 | ≥ 4.5/5 |

---

## 🔗 协作 Skill

| Skill | 协作方式 |
|-------|----------|
| `competitor-analyzer` | 竞品数据采集 → 清洗 → 分析 |
| `lead-generator` | 线索数据清洗 → 画像评分 |
| `seo-auditor` | SEO 数据采集 → 清洗 → 分析 |
| `content-writer` | 数据洞察 → 内容生产 |
| `lead-generator` | 清洗后线索 → 画像评分 |

---

## 🚀 部署到 Hermes

```bash
mkdir -p ~/.hermes/skills/revenue/data-scraper/scripts

cat > ~/.hermes/skills/revenue/data-scraper/scripts/validate.py << 'EOF'
#!/usr/bin/env python3
import shutil, subprocess, sys

checks = {
    "python3": ["python3", "--version"],
    "pandas": ["python3", "-c", "import pandas; print(pandas.__version__)"],
    "polars": ["python3", "-c", "import polars; print(polars.__version__)"],
    "playwright": ["python3", "-c", "import playwright; print(playwright.__version__)"],
    "beautifulsoup4": ["python3", "-c", "import bs4; print(bs4.__version__)"],
    "lxml": ["python3", "-c", "import lxml; print(lxml.__version__)"],
    "openpyxl": ["python3", "-c", "import openpyxl; print(openpyxl.__version__)"],
    "polars": ["python3", "-c", "import polars; print(polars.__version__)"],
    "duckdb": ["python3", "-c", "import duckdb; print(duckdb.__version__)"],
}

all_ok = True
for name, cmd in [
    ("python3", ["python3", "--version"]),
    ("pandas", ["python3", "-c", "import pandas; print(pandas.__version__)"]),
    ("polars", ["python3", "-c", "import polars; print(polars.__version__)"]),
    ("playwright", ["python3", "-c", "import playwright; print(playwright.__version__)"]),
    ("bs4", ["python3", "-c", "import bs4; print(bs4.__version__)"]),
    ("lxml", ["python3", "-c", "import lxml; print(lxml.__version__)"]),
    ("openpyxl", ["python3", "-c", "import openpyxl; print(openpyxl.__version__)"]),
    ("duckdb", ["python3", "-c", "import duckdb; print(duckdb.__version__)"]),
]:
    try:
        import subprocess
        subprocess.run(cmd, capture_output=True, timeout=10, check=True)
        print(f"✅ {cmd[0]}: OK")
    except:
        print(f"❌ {cmd[0]}: MISSING (可后续安装)")

print("Data Scraper 环境检查完成")
EOF
```