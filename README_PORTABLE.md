# DeepSeek GEO Collector 跨电脑迁移说明

本项目支持 Windows 环境下的低门槛迁移。

---

## 一、当前电脑：生成迁移包

直接双击：

`build_portable_package.bat`

生成的迁移 ZIP 位于：

`dist/`

文件名类似：

`deepseek_geo_collector_portable_20260918_112816.zip`

迁移包会自动排除：

- `.venv/`
- `browser_profile/`
- `output/`
- `.git/`
- `.idea/`
- `__pycache__/`
- `.pytest_cache/`
- `.env`

因此不会携带当前电脑的虚拟环境、登录状态、运行结果和本机配置。

---

## 二、新电脑：准备基础软件

建议提前安装：

- Python 3.11
- Google Chrome
- Ollama

Python 建议使用 3.11，与项目开发和测试环境保持一致。

---

## 三、新电脑：解压项目

将迁移 ZIP 解压到任意英文路径，例如：

`D:\deepseek_geo_collector`

建议避免路径过深。

---

## 四、新电脑：初始化环境

进入项目目录后，直接双击：

`setup_new_pc.bat`

脚本会自动执行：

- 检测 Python 3.11
- 创建 `.venv`
- 安装项目依赖
- 安装 pytest 等开发依赖
- 检测 Chrome
- 生成新电脑自己的 `.env`
- 创建 `browser_profile`
- 创建 `output`
- 检测 Ollama
- 检测 `qwen2.5:7b`
- 执行项目环境自检

如果 Ollama 已安装但缺少模型，可执行：

```powershell
ollama pull qwen2.5:7b