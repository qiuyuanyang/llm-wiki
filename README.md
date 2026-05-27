# LLM Wiki — 基础设施知识库

基于 Andrej Karpathy 的 [llm-wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 模式构建的 IT 运维知识库系统。

LLM Agent 自动将原始文档转化为结构化 wiki，支持语义搜索和智能问答。

---

## 快速开始

```bash
# 1. 将项目克隆并作为 Obsidian Vault 打开（打开项目根目录，不是 wiki/）
# 2. 将文档放入 raw/sources/
# 3. 启动守护进程（自动处理新文件）
./llm-wiki-start.sh

# 或手动导入单个文件
./wiki.sh ingest ~/Downloads/文档.pdf

# 生成向量索引（需要 embedding 模型运行中）
./wiki.sh embed

# 提问
./wiki.sh query "web-server-01 的 IP 地址是多少？"
```

安装 Python 依赖：

```bash
# 方式一：使用 requires.txt 一键安装（推荐）
pip install -r requires.txt

# 方式二：手动安装
pip install anthropic openai watchdog rich flask pdfplumber python-docx openpyxl xlrd json-repair
```

---

## 目录结构

```
.
├── LICENSE                    # MIT 许可证
├── README.md                  # 本文件
├── wiki_config.json           # 模型配置（提供商 / 模型选择）
├── config.py                  # 集中配置（环境变量 + JSON）
├── wiki.sh                    # 统一 CLI 入口
├── LLM.md                     # LLM Agent 操作指南（自动加载）
│
├── llm-wiki-start.sh          # 一键启动脚本
├── llm-wiki-stop.sh           # 一键停止脚本
│
├── wiki/                      # LLM 生成的 wiki 内容（只读）
│   ├── index.md               # 内容索引 — 每次导入更新
│   ├── log.md                 # 操作日志 — 只追加
│   ├── overview.md            # 全局知识综合
│   ├── entities/              # 人物、组织、产品、地点
│   ├── concepts/              # 术语、理论、方法、框架
│   ├── infrastructure/        # 服务器、交换机、防火墙、数据库、服务
│   ├── sources/               # 源文档摘要页面（与 raw/sources/ 一一对应）
│   ├── queries/               # 高价值问答归档
│   ├── comparisons/           # 对比分析
│   └── diagnoses/             # 故障诊断页面
│
├── raw/                       # 源材料（只读 — LLM 不会修改）
│   ├── sources/               # 放文档到这里触发导入
│   ├── assets/                # 图片和附件
│   └── clips/                 # Obsidian Web Clipper 输出
│
├── scripts/                   # 自动化工具
│   ├── wiki_watcher.py        # 守护进程（监控 raw/ 自动导入）
│   ├── vector_ingest.py       # 生成向量嵌入
│   ├── query_engine.py        # 智能问答（向量搜索 + LLM）
│   ├── diagnosis_engine.py    # 故障诊断知识引擎（支持语义搜索）
│   ├── graph_viz.py           # D3 拓扑图生成器
│   ├── web_ui.py              # Web 界面
│   ├── stats.sh               # 统计和健康检查
│   ├── search.sh              # 全文搜索
│   ├── clean_orphans.py       # 孤儿向量清理脚本
│   └── templates/             # Web 页面模板
│
├── vector_store.py            # SQLite 向量存储
├── embedding_client.py        # OpenAI 兼容 embedding API 客户端
├── requires.txt               # Python 依赖清单（pip install -r requires.txt）
└── templates/                 # Obsidian Templater 模板
    └── infrastructure-template.md  # 基础设施组件模板
```

---

## 工作流程

| 操作  | 你做的                                           | LLM 做的                                                    |
|---------|--------------------------------------------------|-------------------------------------------------------------|
| 导入  | 放入文件到 `raw/sources/` 或 `./wiki.sh ingest <file>` | 读取、提炼、更新 10-15 个页面，自动同步向量索引 |
| 查询  | 向 LLM Agent 提问                     | 读取索引 → 深入相关页面 → 综合回答；可选归档 |
| 搜索  | `./wiki.sh search <关键词>`              | 全文搜索 wiki 内容 |
| 语义搜索 | `./wiki.sh query <问题>`               | 向量搜索 + LLM 综合回答 |
| 诊断搜索 | `./wiki.sh diagnose search "问题描述"`     | 语义匹配故障记录（症状 → 原因 → 解决方案） |

---

## 功能特性

### 🔍 语义搜索与智能问答

基于 embedding 模型（如 Qwen3-Embedding-8B）的语义搜索。通过语义含义查找相关页面，不仅是关键词匹配。

```bash
# 生成所有 wiki 页面的向量索引
./wiki.sh embed

# 提问 — 向量搜索 + LLM 综合回答
./wiki.sh query "如何配置 MySQL 主从复制？"

# 仅向量搜索（不调用 LLM）
./wiki.sh search-v "防火墙规则"
```

### 📊 基础设施拓扑图

交互式 D3 力导向图，展示基础设施组件之间的依赖关系。

```bash
./wiki.sh graph
# 生成 wiki/topology.html 在浏览器中打开
```

### 🔧 故障诊断引擎

从文档中自动提取 **问题 → 原因 → 解决方案** 三元组，支持语义搜索。

```bash
# 扫描源文档提取诊断三元组
./wiki.sh diagnose scan

# 语义搜索故障问题
./wiki.sh diagnose search "数据库连接断开"

# 列出所有诊断记录
./wiki.sh diagnose list

# 查看统计
./wiki.sh diagnose stats
```

### 🌐 Web 界面

通过浏览器浏览、搜索和查询 wiki。

```bash
./wiki.sh web              # 启动 Web UI，端口 5000
./wiki.sh web --port 8080  # 自定义端口
```

功能：
- 📊 统计仪表板（页面类型分布，中文名称显示）
- 📄 最近页面（自动提取中文标题，存储保持英文）
- 🔍 语义搜索
- 🤖 智能问答（Markdown 渲染回答）
- 🔧 故障诊断浏览器
- 📊 交互式拓扑图

> **中文标题显示**：首页和搜索页的页面名称自动从 Markdown 正文的 `# 一级标题` 提取中文显示，存储层（文件名/路径）保持英文不变。

### 🏗️ 基础设施实体支持

新增基础设施页面类型：服务器、交换机、防火墙、数据库、服务、存储、监控。每个组件有独立页面，包含依赖关系、IP 地址和配置摘要。

模板：`templates/infrastructure-template.md`

### ⚡ 自动向量同步

每次导入新文档后，系统自动同步向量索引，搜索和问答立即可用。

### 🧹 孤儿向量自动清理

当 wiki 页面被删除时，向量库可能残留孤儿条目。系统提供三层清理机制：

- **异步后台清理**：删除源文件时自动在后台线程清理，不阻塞主流程
- **定时自动清理**：crontab 每天凌晨 3:00 自动扫描清理
- **手动清理**：`./wiki.sh clean-orphans` 或 `POST /api/vectors/cleanup-orphan`

```bash
# 手动执行
./wiki.sh clean-orphans

# 安静模式（适合脚本/cron）
./wiki.sh clean-orphans --cron
```

---

## 模型配置

随时切换模型 — 无需修改代码：

```bash
./wiki.sh model local,Qwen3.6-35B-A3B-FP8     # 本地 Ollama / vLLM
./wiki.sh model dashscope,qwen-max             # 阿里云 DashScope
./wiki.sh model anthropic,claude-sonnet-4-6   # Anthropic（默认）
./wiki.sh model openai,gpt-4o                 # OpenAI

# 查看当前模型
./wiki.sh model
```

配置持久化到 `wiki_config.json`。编辑 `providers` 对象可添加自定义提供商：

```json
"minimax": {
  "base_url": "https://api.minimax.chat/v1",
  "api_key_env": "MINIMAX_API_KEY"
}
```

### 内置提供商

| 提供商    | API 端点                      | 环境变量          |
|-------------|-------------------------------|-------------------|
| `anthropic` | Anthropic 官方                | `ANTHROPIC_API_KEY` |
| `local`     | `http://localhost:11434/v1`   | 无（Ollama 默认） |
| `dashscope` | DashScope 兼容端点            | `DASHSCOPE_API_KEY` |
| `openai`    | OpenAI 官方                   | `OPENAI_API_KEY`  |

---

## 环境变量

所有模型端点和 API 密钥通过环境变量配置 — **不硬编码密钥**。

### Embedding 模型

| 变量 | 默认值 | 说明 |
|---|---|---|
| `EMBEDDING_API_BASE_URL` | `http://localhost:8000/v1` | OpenAI 兼容 embedding 端点 |
| `EMBEDDING_MODEL` | `Qwen3-Embedding-8B` | Embedding 模型名称 |
| `EMBEDDING_API_KEY` | (无) | Embedding 服务 API 密钥 |
| `EMBEDDING_DIM` | `4096` | Embedding 向量维度 |

### LLM 模型

| 变量 | 默认值 | 说明 |
|---|---|---|
| `LLM_API_BASE_URL` | `http://localhost:8000/v1` | OpenAI 兼容 LLM 端点 |
| `LLM_MODEL` | `Qwen3.6-35B-A3B-FP8` | 导入/查询/检查用 LLM 模型 |
| `LLM_API_KEY` | (无) | LLM 服务 API 密钥 |

### 其他

| 变量 | 默认值 | 说明 |
|---|---|---|
| `WIKI_ROOT` | `.`（当前目录） | Wiki 根目录路径 |

---

## 命令参考

```bash
# ── 服务管理 ──
./llm-wiki-start.sh            # 一键启动所有服务
./llm-wiki-stop.sh             # 一键停止所有服务
./wiki.sh daemon               # 启动后台守护进程
./wiki.sh start                # 启动前台监视器
./wiki.sh stop                 # 停止守护进程
./wiki.sh status               # 查看运行状态和当前模型

# ── 文档处理 ──
./wiki.sh ingest <file|URL>    # 手动导入源材料
./wiki.sh stats                # 显示 wiki 统计
./wiki.sh lint                 # 运行健康检查

# ── 搜索与查询 ──
./wiki.sh search <关键词>       # 全文搜索
./wiki.sh query <问题>          # 智能问答（向量搜索 + LLM）
./wiki.sh search-v <关键词>     # 仅向量搜索（不调用 LLM）

# ── 向量索引 ──
./wiki.sh embed                # 生成向量嵌入
./wiki.sh reindex              # 完全重建索引
./wiki.sh clean-orphans        # 清理孤儿向量条目（wiki 已删但向量残留）

# 孤儿向量自动清理：每天凌晨 3:00 通过 crontab 自动执行

# ── 故障诊断 ──
./wiki.sh diagnose scan        # 扫描提取诊断三元组
./wiki.sh diagnose search "关键词" # 语义搜索故障
./wiki.sh diagnose list        # 列出所有诊断记录
./wiki.sh diagnose stats       # 诊断统计

# ── Web UI ──
./wiki.sh web                  # 启动 Web UI（默认端口 5000）
./wiki.sh web --port 8080      # 自定义端口

# ── 其他 ──
./wiki.sh hotspot              # 立即生成热点分析
./wiki.sh graph                # 生成拓扑图（HTML）
./wiki.sh model [SPEC]         # 查看或切换当前模型
```

---

## Python 依赖

所有第三方包已列在 `requires.txt` 中：

| 包 | 用途 |
|---|---|
| anthropic | Anthropic Claude API 调用 |
| openai | OpenAI 兼容 API（含 Embedding） |
| watchdog | 文件监控（守护进程） |
| rich | 终端富文本输出 |
| flask | Web UI 服务框架 |
| pdfplumber | PDF 文档解析 |
| python-docx | Word (.docx) 文档解析 |
| openpyxl | Excel (.xlsx) 文件解析 |
| xlrd | Excel (.xls) 文件解析 |
| json-repair | 容错 JSON 解析（修复 LLM 输出） |

安装：`pip install -r requires.txt`

---

## 许可证

本项目基于 [MIT License](LICENSE) 发布。
