# LLM Wiki — 维护手册

---

## 目录结构

```
llm-wiki/                        ← Obsidian Vault 根目录（打开此目录）
├── LLM.md                       ← LLM Agent 操作指南（核心 — 不要随意修改）
├── wiki_config.json             ← 当前模型配置
├── wiki.sh                      ← 统一 CLI 入口
│
├── wiki/                        ← LLM 生成内容（你只需阅读）
│   ├── index.md                 ← 内容索引（每次导入自动更新）
│   ├── log.md                   ← 操作日志（只追加）
│   ├── overview.md              ← 全局知识综合
│   ├── entities/                ← 人物 / 组织 / 产品
│   ├── concepts/                ← 术语 / 理论 / 方法
│   ├── infrastructure/          ← 服务器 / 交换机 / 防火墙 / 数据库 / 服务
│   ├── sources/                 ← 源文档摘要（与 raw/sources/ 一一对应）
│   ├── queries/                 ← 高价值问答归档
│   ├── comparisons/             ← 对比分析
│   └── diagnoses/               ← 故障诊断页面
│
├── raw/                         ← 你放文件，LLM 读取（只读 — 不修改）
│   ├── sources/                 ← 源材料（放文件到这里触发导入）
│   ├── assets/                  ← 图片附件
│   └── clips/                   ← Obsidian Web Clipper 输出
│
├── templates/                   ← Obsidian Templater 模板
└── scripts/                     ← 自动化脚本
    ├── wiki_watcher.py          ← 守护进程（监控 raw/ 自动处理）
    ├── vector_ingest.py         ← 生成向量嵌入
    ├── query_engine.py          ← 智能问答（向量搜索 + LLM）
    ├── diagnosis_engine.py      ← 故障诊断知识引擎（支持语义搜索）
    ├── graph_viz.py             ← D3 拓扑图生成器
    ├── web_ui.py                ← Web 界面
    ├── stats.sh                 ← 统计和健康检查
    ├── search.sh                ← 全文搜索
    └── templates/               ← Web 页面模板
```

---

## 首次设置

**1. 将项目根目录作为 Obsidian Vault 打开**（不是 `wiki/` 子目录）

```
Obsidian → 打开 Vault → 选择 llm-wiki/
```

`.obsidian/` 已预配置：附件 → `raw/assets/`，模板 → `templates/`，图颜色已设置。

**2. 安装 Obsidian 插件**（设置 → 社区插件）

| 插件        | 用途                          | 优先级    |
|---------------|------------------------------|-------------|
| **Dataview**  | `dashboard.md` 动态表格       | 必需        |
| **Templater** | 快速创建符合规范的页面        | 必需        |
| Obsidian Git  | 自动备份                      | 推荐        |

---

## 三种运行模式

### 模式 A：手动（完全控制 — 适合重要文档）

```bash
./wiki.sh ingest ~/Downloads/文档.pdf
# → 打印提示，复制给 LLM Agent
```

### 模式 B：前台（实时日志可见）

```bash
./wiki.sh start
# 放文件到 raw/sources/ → 自动处理，终端显示处理结果
```

### 模式 C：后台守护进程（全自动 — 日常推荐）

```bash
./wiki.sh daemon    # 后台启动
./wiki.sh status    # 查看状态
./wiki.sh stop      # 停止
```

或使用一键脚本：

```bash
./llm-wiki-start.sh    # 一键启动所有服务
./llm-wiki-stop.sh     # 一键停止所有服务
```

安装依赖（仅模式 B/C 需要）：

```bash
pip install anthropic openai watchdog rich flask pdfplumber
```

---

## 核心操作

### 导入 — 处理新文档

告诉 LLM Agent：`请处理 raw/sources/xxx.md`

LLM 会：读取 → 报告 3-5 个关键发现 → 创建摘要页面 → 更新实体/概念页面 → 更新 `index.md` 和 `log.md` → 自动同步向量索引

### 查询 — 提问

直接向 LLM Agent 提问。它会读取 `index.md` 找到相关页面，综合回答，并询问是否归档到 `wiki/queries/`。

也可以用命令行：

```bash
./wiki.sh query "web-server-01 的 IP 地址是多少？"
./wiki.sh search-v "防火墙规则"          # 仅向量搜索
```

### 搜索 — 语义 + 关键词

```bash
./wiki.sh search "关键词"                # 全文搜索
./wiki.sh diagnose search "问题描述"    # 语义搜索故障诊断
```

### 健康检查

```bash
./wiki.sh lint
# 然后告诉 LLM Agent："请运行 LINT 健康检查"
```

---

## 模型配置

模型配置存储在 `wiki_config.json` 中，通过 `./wiki.sh model` 切换 — 无需修改代码。

### 切换命令

```bash
./wiki.sh model                                # 查看当前模型
./wiki.sh model local,Qwen3.6-35B-A3B-FP8     # 本地 Ollama / vLLM
./wiki.sh model dashscope,qwen-max            # 阿里云 DashScope
./wiki.sh model anthropic,claude-sonnet-4-6  # Anthropic
./wiki.sh model openai,gpt-4o                # OpenAI
```

### 内置提供商

| 提供商    | API 端点                      | 环境变量          |
|-------------|-------------------------------|-------------------|
| `anthropic` | Anthropic 官方                | `ANTHROPIC_API_KEY` |
| `local`     | `http://localhost:11434/v1`   | 无（Ollama 默认） |
| `dashscope` | DashScope 兼容端点            | `DASHSCOPE_API_KEY` |
| `openai`    | OpenAI 官方                   | `OPENAI_API_KEY`  |

### 添加自定义提供商

编辑 `wiki_config.json`，在 `providers` 下添加：

```json
"minimax": {
  "base_url": "https://api.minimax.chat/v1",
  "api_key_env": "MINIMAX_API_KEY"
}
```

然后 `./wiki.sh model minimax,abab7-chat-preview` 立即生效。

---

## 链接规范

Vault 根目录是项目根目录。内部链接必须包含 `wiki/` 前缀：

```
正确：[[wiki/entities/geoffrey-hinton|Geoffrey Hinton]]
正确：[[wiki/concepts/attention-mechanism]]
错误：  [[entities/geoffrey-hinton]]
```

---

## 定期维护

| 频率          | 操作                                                              |
|--------------------|---------------------------------------------------------------------|
| 每次新源文档   | 放入 `raw/sources/` → LLM 自动处理并同步向量 |
| 每周             | `./wiki.sh lint` → 让 LLM Agent 修复报告的问题 |
| 每月             | `./wiki.sh hotspot` → 生成知识热点分析 |

---

## 快速参考

```bash
./llm-wiki-start.sh                # 一键启动所有服务
./llm-wiki-stop.sh                 # 一键停止所有服务
./wiki.sh daemon                   # 后台守护进程
./wiki.sh status                   # 查看状态和模型
./wiki.sh ingest <file|URL>       # 导入源材料
./wiki.sh model [SPEC]            # 查看/切换模型
./wiki.sh stats                   # wiki 统计
./wiki.sh lint                    # 健康检查
./wiki.sh search "关键词"          # 全文搜索
./wiki.sh query <问题>             # 智能问答
./wiki.sh search-v <关键词>        # 仅向量搜索
./wiki.sh embed                   # 生成向量嵌入
./wiki.sh reindex                 # 完全重建索引
./wiki.sh diagnose scan           # 扫描诊断三元组
./wiki.sh diagnose search "问题"   # 语义搜索故障
./wiki.sh web                     # 启动 Web UI（端口 5000）
./wiki.sh graph                   # 生成拓扑图
./wiki.sh hotspot                 # 热点分析
```
