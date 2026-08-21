# DeepSeek GEO Collector

DeepSeek GEO Collector 是一个独立的 DeepSeek 网页 GEO 数据采集系统。

## 项目目标

负责从 DeepSeek 网页端采集 GEO 分析所需的：

* 问题
* 回答正文
* Sources / 引用信源
* 页面截图
* Validation
* Batch 数据
* GEO 标准 Package

最终输出兼容：

`geo_package_v1`

以供下游 GEO 分析展示系统统一导入。

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
* 页面截图
* DeepSeek 主模式 DOM 探测与自动化测试

当前已完成 Quick / Expert 两种模式的基础回答采集能力。

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

现阶段 Expert 模式仅采集：

* 问题
* 回答正文
* 页面截图
* 相关任务状态及后续 Validation 数据

不进行网页 Sources 采集。

如果后续 DeepSeek Expert 模式增加搜索、Citation 或参考来源能力，将重新进行 DOM 探测，并评估恢复 Expert Sources Collector
的开发。

## Python

Python >= 3.11
