# DeepSeek GEO Collector

DeepSeek GEO Collector 是一个独立的 DeepSeek 网页 GEO 数据采集系统。

项目通过 Playwright 自动操作 DeepSeek 网页端，完成 Quick / Expert 模式下的问题批量采集、回答正文提取、Quick Sources
采集、Validation、批量任务编排以及 `geo_package_v1` 标准数据包导出。

最终数据可供下游 GEO 分析展示系统统一导入。

---

## 项目目标

负责从 DeepSeek 网页端采集 GEO 分析所需的：

* 问题
* 回答正文
* Quick Sources / 引用信源
* 页面截图
* 页面 HTML 证据
* Validation
* Batch 数据
* GEO 标准 Package

最终输出兼容：

`geo_package_v1`

供下游 GEO 分析系统进一步完成：

* 提及分析
* 情感 / 中正分析
* 信源分析
* GEO 指标统计
* 可视化展示

DeepSeek GEO Collector 当前主要负责：

> **可靠采集、基础质量校验以及标准化数据输出。**

---

## 当前开发阶段

项目已完成：

* 项目基础骨架与 Core Models
* `geo_package_v1` 导出与校验
* Playwright 持久化浏览器会话
* DeepSeek 登录状态持久化
* Quick 模式切换与单题回答采集
* Expert 模式切换与单题回答采集
* Answer Waiter 回答完成检测
* Answer Parser 正文提取与清洗
* Quick Sources / 引用信源采集
* 页面截图与 HTML 证据保存
* 标准失败分类
* Retryable Failure 判断
* 网络 / 超时失败自动重试
* CSV Batch 输入校验
* Batch 串行任务执行
* 单任务失败隔离
* 不同任务之间的执行间隔控制
* Batch 结果导出为 `geo_package_v1`
* 多任务 JSONL 标准序列化
* GEO Package 完整性校验
* 采集结果 Validation
* 正式 Pipeline 编排层
* 正式 CLI 运行入口
* Pipeline Unit / Integration Test
* DeepSeek 真实网页 Batch Smoke 验证

当前正式生产链路已经形成：

```text
CSV
 ↓
LOAD
 ↓
COLLECT
 ↓
VALIDATE
 ↓
BATCH RESULT
 ↓
PACKAGE
 ↓
VERIFY
 ↓
CLI RESULT
```

Quick / Expert 两种模式均已完成真实网页批量采集验证。

当前 DeepSeek 页面能力为：

* Quick：支持回答正文与网页 Sources 采集；
* Expert：支持回答正文采集；
* Expert 当前不支持网页搜索和 Sources；
* Expert 无 Sources 属于 DeepSeek 当前平台能力限制；
* Expert 无 Sources 不视为采集失败；
* Expert 回答正文正常时仍可通过 Validation。

---

## DeepSeek 模式说明

### Quick

Quick 模式支持：

* 问题提交
* 回答正文采集
* 智能搜索
* Citation / Sources 采集
* 页面截图
* HTML 证据
* Validation

真实页面验证中，Quick 模式可以正常获得网页 Sources。

---

### Expert

Expert 模式支持：

* 问题提交
* 回答正文采集
* 页面截图
* HTML 证据
* Validation

当前不进行网页 Sources 采集。

---

## Expert Sources 暂缓开发说明

当前版本暂不开发 DeepSeek Expert（专家模式）的网页 Sources / 引用信源采集能力。

在实际页面 DOM 探测和真实单题验证过程中，DeepSeek Expert 模式页面明确提示：

> 专家模式暂不支持搜索，请使用快速模式

同时实际验证发现：

* Expert 模式下智能搜索功能不可用；
* Expert 回答正文不存在网页 Citation 链接；
* 回答区域及其邻近 DOM 中不存在可采集的网页来源链接；
* Expert 模式当前无法获得可靠的网页 Sources 数据。

因此，Expert Sources 暂缓开发属于 **DeepSeek 当前产品能力限制**，并非采集器功能未完成。

现阶段 Expert 模式采集：

* 问题
* 回答正文
* 页面截图
* HTML 证据
* 任务状态
* Validation 结果

Expert 的 Core Sources 状态记录为：

```text
NOT_APPLICABLE
```

在 `geo_package_v1` 协议层映射为：

```text
not_supported
```

该状态表示当前平台模式不具备网页 Sources 能力，不表示回答采集失败。

如果后续 DeepSeek Expert 模式增加搜索、Citation 或参考来源能力，将重新进行 DOM 探测，并评估恢复 Expert Sources Collector
的开发。

---

## Python

要求：

```text
Python >= 3.11
```

当前项目开发环境已在 Python 3.11 下完成测试。

---

## 安装

建议使用独立虚拟环境。

Windows PowerShell 示例：

```powershell
python -m venv .venv
```

激活环境：

```powershell
.\.venv\Scripts\Activate.ps1
```

安装项目依赖：

```powershell
python -m pip install -e .
```

安装开发 / 测试依赖：

```powershell
python -m pip install -e ".[dev]"
```

检查依赖状态：

```powershell
python -m pip check
```

---

## 配置

项目配置通过环境变量读取。

仓库提供：

```text
.env.example
```

本地运行时可根据实际环境创建 `.env`。

浏览器登录状态通过持久化 Browser Profile 保存，因此通常只需要首次完成 DeepSeek 网页登录，后续可以继续复用登录状态。

敏感配置、浏览器 Profile 和运行产物不应提交到 Git。

---

## 正式运行入口

推荐使用正式 Pipeline CLI 执行批量采集：

```powershell
python -m app.pipeline `
--csv input\batch.csv `
--batch-id batch_20260824_001 `
--output-dir output\package `
--product-id hongmao_yaojiu `
--product-name "鸿茅药酒"
```

这是当前项目的正式生产入口。

正式入口会依次执行：

```text
CSV
 ↓
LOAD
 ↓
COLLECT
 ↓
VALIDATE
 ↓
PACKAGE
 ↓
VERIFY
 ↓
CLI RESULT
```

其中：

* `LOAD`：读取并校验 CSV Batch 任务；
* `COLLECT`：执行 DeepSeek Quick / Expert 网页采集；
* `VALIDATE`：判断采集结果是否可以作为有效 GEO 样本；
* `PACKAGE`：导出 `geo_package_v1`；
* `VERIFY`：校验 Package 文件、引用关系和 checksum；
* `CLI RESULT`：输出批次运行摘要和退出码。

---

## Batch CSV 格式

CSV 必须至少包含以下字段：

```csv
question_id,question,mode
Q001,鸿茅药酒是什么？,quick
Q001,鸿茅药酒是什么？,expert
Q002,鸿茅药酒的主要成分有哪些？,quick
Q002,鸿茅药酒的主要成分有哪些？,expert
```

支持的 `mode`：

```text
quick
expert
```

### CSV 编码

输入 CSV 使用：

```text
UTF-8
```

或：

```text
UTF-8 BOM
```

项目 Loader 使用 `utf-8-sig` 读取，可以同时兼容普通 UTF-8 和 UTF-8 BOM。

不建议直接使用 GBK / ANSI 编码 CSV。

---

## Batch Task ID

同一个 `question_id` 可以同时存在 Quick 和 Expert 任务。

系统会自动把模式加入 `task_id`。

例如：

```text
batch_001_Q001_quick
batch_001_Q001_expert
```

因此：

```text
Q001 + quick
```

与：

```text
Q001 + expert
```

属于两个不同任务。

但同一个 Batch 中不允许重复出现相同的：

```text
question_id + mode
```

组合。

例如下面的数据属于重复任务：

```csv
question_id,question,mode
Q001,鸿茅药酒是什么？,quick
Q001,鸿茅药酒是什么？,quick
```

Loader 会直接拒绝该输入。

---

## Batch 执行策略

当前 Batch 使用串行采集。

执行结构：

```text
Task 1
 ↓
等待任务间隔
 ↓
Task 2
 ↓
等待任务间隔
 ↓
Task 3
```

当前没有并发操作 DeepSeek 网页。

这样可以降低：

* 页面状态冲突
* 登录状态异常
* 风控概率
* UI 操作互相干扰
* 浏览器并发不稳定

---

## Retry

系统支持 Retryable Failure 自动重试。

当前主要可重试类型：

```text
NETWORK_ERROR
ANSWER_TIMEOUT
```

例如：

```text
第一次采集
 ↓
ANSWER_TIMEOUT
 ↓
等待 retry interval
 ↓
第二次采集
```

如果达到最大 Retry 次数仍然失败，则保留最终失败结果，并继续执行后续 Batch 任务。

例如：

```text
Q001 SUCCESS
Q002 FAILED
Q003 SUCCESS
```

Q002 的失败不会导致整个 Batch 中断。

---

## Retry Interval 与 Task Interval

系统区分两种等待时间。

### Retry Interval

同一个任务失败后：

```text
Task A Attempt 1
 ↓
失败
 ↓
Retry Interval
 ↓
Task A Attempt 2
```

### Task Interval

不同任务之间：

```text
Task A
 ↓
Task Interval
 ↓
Task B
```

两者语义不同，不混用。

---

## Validation

当前 Validation 的职责是：

> 判断一条采集结果是否可以作为有效 GEO 样本使用。

Validation 不负责判断：

* 回答事实是否正确
* 是否提及目标品牌
* 回答情感正负
* 中正率
* 提及率
* GEO 排名
* 信源质量

这些属于后续 GEO Analysis 阶段。

---

## 当前 Validation 规则

### 任务执行失败

```text
TaskStatus = FAILED
```

结果：

```text
ValidationStatus = FAIL
is_complete = false
```

---

### 回答为空

任务成功，但：

```text
answer_text_clean = ""
```

结果：

```text
ValidationStatus = FAIL
is_complete = false
```

---

### Quick 正常采集

任务成功：

```text
answer 非空
sources = SUCCESS
```

结果：

```text
ValidationStatus = PASS
is_complete = true
```

---

### Quick Sources 部分成功

```text
sources = PARTIAL
```

结果：

```text
ValidationStatus = PASS_WITH_WARNINGS
is_complete = true
```

---

### Quick Sources 失败或不可用

Quick 回答正文正常，但 Sources 采集失败或不可用：

```text
ValidationStatus = PASS_WITH_WARNINGS
is_complete = true
```

回答本身仍然可以作为样本保留，但会记录 Sources Warning。

---

### Expert 无 Sources

Expert 当前：

```text
sources = NOT_APPLICABLE
```

属于正常平台行为。

因此：

```text
Expert 无 Sources
≠ 回答无效
```

只要回答正文正常：

```text
ValidationStatus = PASS
is_complete = true
```

---

## Pipeline 状态

Pipeline 当前存在两种正常完成状态。

### PASS

所有采集任务成功，并且 Package 校验通过：

```text
PASS
```

### PASS_WITH_WARNINGS

Pipeline 正常执行完成、Package 也合法，但存在一个或多个采集失败任务：

```text
PASS_WITH_WARNINGS
```

例如：

```text
TOTAL: 10
SUCCESS: 9
FAILED: 1
```

仍然可以导出完整 Package。

失败任务会被保留在标准数据包中，供下游识别。

---

## Pipeline 退出码

正式 CLI 使用以下退出码。

### 0

```text
PASS
```

含义：

* Pipeline 完整执行成功
* 所有采集任务成功
* Package Verify 成功

---

### 1

```text
PASS_WITH_WARNINGS
```

含义：

* Pipeline 正常执行完成
* Package Verify 成功
* 存在一个或多个采集失败任务

---

### 2

```text
INPUT ERROR
```

例如：

* CSV 文件不存在
* CSV 缺少必需字段
* CSV 存在非法 mode
* CSV 存在空字段
* CSV 存在重复任务
* Batch CSV 为空

---

### 3

```text
PACKAGE VERIFICATION FAILED
```

表示生成的 `geo_package_v1` 未通过完整性校验。

---

未预期的内部程序异常不会被静默吞掉。

例如：

```text
AttributeError
TypeError
内部代码 Bug
```

会直接暴露 traceback，便于开发阶段排查问题。

---

## CLI 输出示例

正常运行示例：

```text
================================================================================
DEEPSEEK GEO PIPELINE
================================================================================
PIPELINE STATUS: PASS
BATCH ID: w10_cli_smoke_002
TOTAL: 4
SUCCESS: 4
FAILED: 0
SUCCESS RATE: 100.00%
PACKAGE: output\package\geo_package_deepseek_w10_cli_smoke_002.zip
PACKAGE VERIFY: PASS
```

---

## geo_package_v1

Pipeline 最终输出：

```text
geo_package_deepseek_<batch_id>.zip
```

例如：

```text
geo_package_deepseek_w10_cli_smoke_002.zip
```

ZIP 中固定包含：

```text
manifest.json
tasks.jsonl
answers.jsonl
sources.jsonl
checksums.json
screenshots/
```

---

## manifest.json

保存批次级信息，例如：

* schema version
* platform
* product
* batch id
* collection modes
* task count
* answer count
* source count
* completed tasks
* valid tasks
* failed tasks
* Pipeline 状态
* 时间信息
* Collector capability

---

## tasks.jsonl

每一行对应一个采集任务。

主要保存：

* task_id
* batch_id
* platform_code
* question_id
* question
* mode_code
* task_status
* error_message
* created_at
* finished_at
* elapsed_seconds

---

## answers.jsonl

每一行对应一条 DeepSeek 回答。

主要保存：

* answer_id
* task_id
* batch_id
* product_id
* question_id
* mode_code
* question_text
* answer_text_raw
* answer_text_clean
* acquisition_status
* validation_status
* is_complete
* source_collection_status
* source_count_raw
* screenshot_path
* collected_at
* platform_meta_json

---

## sources.jsonl

保存 Quick 模式采集到的网页 Sources。

主要包括：

* answer_id
* task_id
* question_id
* mode_code
* source_order
* source_title_raw
* source_site_name_raw
* source_url_raw
* normalized_source_url_raw
* resolved_url
* raw_href
* domain
* source_snippet
* occurrence_id
* search_round
* source_status
* is_valid

URL 会进行标准化处理，并清理常见 Tracking 参数。

---

## checksums.json

保存标准 Package 数据文件的 SHA-256：

```text
manifest.json
tasks.jsonl
answers.jsonl
sources.jsonl
```

Verifier 会重新计算文件 Hash，并检查数据是否被修改。

---

## Package Verify

项目提供严格的 `geo_package_v1` 校验能力。

当前主要检查：

* Package 是否存在
* 必需文件是否完整
* ZIP 路径是否安全
* Schema Version
* GEO Batch Version
* SHA-256 checksum
* task_id 唯一性
* answer_id 唯一性
* occurrence_id 唯一性
* Answer → Task 引用关系
* Source → Task 引用关系
* Source → Answer 引用关系
* Screenshot 引用是否存在

Package Verify 成功时正常返回。

校验失败时抛出：

```text
PackageVerificationError
```

---

## Artifacts

真实网页采集时，每次运行会保存证据文件。

默认结构：

```text
output/
└── artifacts/
    └── <run_id>/
        ├── page.png
        └── page.html
```

其中：

* `page.png`：当前 DeepSeek 页面截图；
* `page.html`：当前页面完整 HTML。

这些文件用于：

* UI 变更排查
* Answer Parser 排查
* Sources 采集排查
* 失败任务回溯
* 页面结构变化调查

---

## Smoke Scripts

`scripts/` 中仍然保留部分探针和 Smoke 工具。

例如：

```text
scripts/smoke_batch.py
```

主要用于：

* 开发阶段真实网页验证
* DOM 探测
* Selector 调试
* Answer / Sources 调试
* Package Smoke Test

正式生产运行优先使用：

```powershell
python -m app.pipeline
```

而不是 Smoke Script。

---

## 测试

运行全部测试：

```powershell
python -m pytest -q
```

运行指定测试：

```powershell
python -m pytest tests/unit/test_runner.py -q
```

例如 Pipeline：

```powershell
python -m pytest tests/unit/test_pipeline_runner.py -q
```

Validation：

```powershell
python -m pytest tests/unit/test_validator.py -q
```

Pipeline Integration：

```powershell
python -m pytest tests/integration/test_pipeline_integration.py -q
```

---

## 代码编译检查

检查 `app` 与 `scripts`：

```powershell
python -m compileall app scripts
```

---

## Python 依赖检查

```powershell
python -m pip check
```

正常结果：

```text
No broken requirements found.
```

---

## Git 提交前检查

推荐每次提交前执行：

```powershell
python -m pytest -q
python -m pip check
python -m compileall app scripts
git diff --check
git status --short
```

暂存后：

```powershell
git diff --cached --check
git diff --cached --stat
git status --short
```

---

## 项目目录

当前核心结构：

```text
deepseek_geo_collector/
├── app/
│   ├── batch/
│   │   ├── export.py
│   │   ├── loader.py
│   │   ├── models.py
│   │   ├── reporter.py
│   │   └── runner.py
│   │
│   ├── browser/
│   │   └── session.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── enums.py
│   │   └── models.py
│   │
│   ├── deepseek/
│   │   ├── answer_parser.py
│   │   ├── answer_waiter.py
│   │   ├── artifact.py
│   │   ├── error_classifier.py
│   │   ├── page.py
│   │   ├── runner.py
│   │   ├── selectors.py
│   │   ├── source_collector.py
│   │   └── source_parser.py
│   │
│   ├── package/
│   │   ├── checksum.py
│   │   ├── constants.py
│   │   ├── exporter.py
│   │   ├── mapping.py
│   │   ├── models.py
│   │   ├── serialization.py
│   │   ├── source_utils.py
│   │   └── verifier.py
│   │
│   ├── pipeline/
│   │   ├── __init__.py
│   │   ├── __main__.py
│   │   ├── models.py
│   │   └── runner.py
│   │
│   └── validation/
│       ├── __init__.py
│       └── validator.py
│
├── scripts/
├── tests/
│   ├── integration/
│   └── unit/
│
├── .env.example
├── pyproject.toml
└── README.md
```

---

## 架构职责

当前系统按职责分层：

```text
Browser
   ↓
DeepSeek Page / Selector
   ↓
Answer / Source Collector
   ↓
GeoRunResult
   ↓
Validation
   ↓
Batch
   ↓
Pipeline
   ↓
geo_package_v1
   ↓
Package Verifier
```

各层主要职责：

### Browser

负责：

* Playwright 生命周期
* Browser Profile
* Page 创建
* DeepSeek 会话环境

### DeepSeek

负责：

* 页面模式操作
* 问题提交
* 回答等待
* Answer Parsing
* Sources 采集
* Artifacts
* 失败分类

### Validation

负责：

* 判断采集结果是否完整
* 判断结果能否成为有效 GEO 样本

### Batch

负责：

* CSV Loader
* Batch Task
* Retry
* Task Interval
* Failure Isolation
* Batch Summary

### Pipeline

负责：

* 正式业务编排
* Load
* Collect
* Validate
* Package
* Verify

### Package

负责：

* `geo_package_v1` 映射
* JSON / JSONL 序列化
* Sources 标准化
* ZIP 导出
* Checksum
* Package Verification

---

## GEO Analysis 边界

当前 DeepSeek GEO Collector 不直接负责最终业务指标计算。

后续 GEO Analysis 层可以基于标准 Package 进一步完成：

```text
Mention Analysis
 ↓
Sentiment Analysis
 ↓
Source Analysis
 ↓
Batch Metrics
```

例如：

* 提及率
* 中正率
* 正向率
* 中性率
* 负向率
* 信源统计
* 信源排名
* Source TopN
* 品牌对比
* 多平台对比

这样 DeepSeek、豆包以及后续其他模型平台都可以通过统一 `geo_package_v1` 接入同一套 GEO Analysis 系统。

---

## 当前状态

DeepSeek GEO Collector 当前已经完成：

```text
单题采集
    ↓
Quick Sources
    ↓
Expert 模式
    ↓
Artifacts
    ↓
Failure Classification
    ↓
Batch
    ↓
Retry
    ↓
Validation
    ↓
Pipeline
    ↓
CLI
    ↓
geo_package_v1
    ↓
Package Verify
```

并已经完成真实 DeepSeek 网页批量运行验证。

当前项目已具备完整的 DeepSeek GEO 批量采集和标准化输出主链路。