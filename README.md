# DeepSeek GEO Collector

DeepSeek GEO Collector 是一个独立的 DeepSeek 网页 GEO 数据采集系统。

## 项目目标

负责从 DeepSeek 网页端采集 GEO 分析所需的：

- 问题
- 回答正文
- Sources / 引用信源
- 页面截图
- Validation
- Batch 数据
- GEO 标准 Package

最终输出兼容：

`geo_package_v1`

以供下游 GEO 分析展示系统统一导入。

## 当前开发阶段

W2：Project Skeleton & Core Models

当前阶段暂不实现：

- DeepSeek 网页自动化
- Playwright
- DOM Selector
- Answer Parser
- Source Parser
- Batch 实际采集

## Python

Python >= 3.11