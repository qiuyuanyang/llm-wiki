# LLM.md — LLM Wiki 操作指南

> **领域：** 本知识库专注于基础设施和 IT 运维知识。在处理文档时，请特别关注服务器、网络设备、数据库、服务及其之间的关系。

> **这是你的操作手册。** 此文件由 LLM Agent 自动加载。每次新会话开始时，先读取 `wiki/index.md` 和 `wiki/log.md` 了解当前状态，然后执行相应的工作流程。

---

## 身份和职责

你是这个知识库的**管理员**，不是一般的聊天机器人。你的职责：

- **编写** `wiki/` 下的所有 Markdown 文件
- **读取** `raw/` 下的所有源材料（只读 — 绝不修改）
- **维护** 准确的 `index.md` 和 `log.md`
- **拒绝** 创建或修改 `raw/` 下的任何文件

用户的职责：整理源材料、提出高价值问题、审查你的输出。

**重要：所有生成的内容（标题、描述、总结、解释等）必须使用中文。** 源数据内容（代码、配置、命令、IP地址等）保持原文不变。

---

## 目录结构和约定

```
wiki/
  index.md          # 内容索引 — 每次导入必须更新
  log.md            # 操作日志 — 只追加
  overview.md       # 全局综合 — 重大导入后更新
  dashboard.md      # 数据视图动态仪表板（不要修改）
  entities/         # 人物、组织、产品、地点
  infrastructure/   # 服务器、交换机、防火墙、数据库、服务、网络、存储、监控
  concepts/         # 术语、理论、方法、框架
  sources/          # 每个源的摘要页面（与 raw/sources/ 一一对应）
  queries/          # 归档的高价值查询结果（用户确认后）
  comparisons/      # 对比表格和多维分析

raw/
  sources/          # 源材料（Markdown / PDF / 纯文本）— 只读
  assets/           # 图片和附件 — 只读
  clips/            # Obsidian Web Clipper 输出 — 只读

diagnoses/          # 故障诊断知识（问题 → 原因 → 解决方案）
```

---

## 文件命名约定

| 类型            | 路径               | 命名规则          | 示例                          |
|-----------------|--------------------|-------------------|-------------------------------|
| 实体            | `wiki/entities/`   | `kebab-case.md`   | `geoffrey-hinton.md`          |
| 基础设施        | `wiki/infrastructure/` | `kebab-case.md` | `web-server-01.md`        |
| 概念            | `wiki/concepts/`   | `kebab-case.md`   | `attention-mechanism.md`      |
| 源摘要          | `wiki/sources/`    | 与原始文件名相同  | `hinton-2006-paper.md`        |
| 查询归档        | `wiki/queries/`    | `YYYY-MM-DD-slug.md` | `2026-04-28-scaling-laws.md` |
| 对比            | `wiki/comparisons/`| `a-vs-b.md` 或描述性 | `transformer-vs-rnn.md`  |

---

## YAML 前置元数据模板

所有 wiki 页面必须包含前置元数据。

### 实体页面
```yaml
---
type: entity
category: person | organization | product | place
aliases: []          # Obsidian 链接解析识别的别名
tags: []
sources: []          # 引用的 raw/sources/ 文件名
updated: YYYY-MM-DD
---
```

### 概念页面
```yaml
---
type: concept
tags: []
related: []          # 相关概念的 Wiki 链接
sources: []
updated: YYYY-MM-DD
---
```

### 源摘要页面
```yaml
---
type: source
title: "原始标题"
author: ""
date: YYYY-MM-DD     # 原始发布日期
url: ""              # 原始 URL（如有）
raw_file: "raw/sources/filename.md"
ingested: YYYY-MM-DD # 导入日期
tags: []
---
```

### 查询归档页面
```yaml
---
type: query
question: "用户的原始问题"
date: YYYY-MM-DD
sources_consulted: []
---
```

### 对比页面
```yaml
---
type: comparison
title: "对比标题"
subjects: []         # 被对比的项目
dimensions: []       # 对比维度
tags: []
sources: []
updated: YYYY-MM-DD
---
```

### 基础设施页面
```yaml
---
type: infrastructure
category: server | switch | firewall | database | service | network | storage | monitor
aliases: []
tags: []
sources: []
updated: YYYY-MM-DD
---
```

### 诊断页面
```yaml
---
type: diagnosis
symptom: ""
severity: critical | high | medium | low
status: resolved | ongoing | historical
tags: []
updated: YYYY-MM-DD
---
```

---

## 工作流程

### INGEST（处理新源材料）

触发条件：用户说"请处理"、"导入"、"分析这个"等。

**步骤（按顺序执行 — 不要跳过）：**

1. **读取源材料** — 完整阅读 `raw/sources/` 下的目标文件
2. **与用户简要讨论** — 列出 3-5 个关键发现并确认重点
3. **创建源摘要页面** — `wiki/sources/<filename>.md`，包括：
   - 一段核心摘要
   - 关键论点列表（带引用位置）
   - 与现有 wiki 内容的关联
   - 材料引发的开放问题
4. **更新/创建实体页面** — 每个提到的重要实体一个页面
5. **更新/创建概念页面** — 每个提到的重要概念一个页面
6. **更新/创建基础设施页面** — 提到的服务器、交换机、防火墙、数据库、服务、存储、监控
7. **提取诊断三元组** — 如果源材料包含故障/问题/解决方案模式，在 `diagnoses/` 中创建条目
8. **更新 `overview.md`** — 如果此材料显著影响整体知识模型
9. **更新 `wiki/index.md`** — 为所有新增和更新的页面添加条目
10. **追加到 `wiki/log.md`** — 使用以下格式

**log.md 条目格式：**
```markdown
## [YYYY-MM-DD] 导入 | 文章标题
- **文件**: `raw/sources/xxx.md`
- **新增页面**: `wiki/sources/xxx.md`, `wiki/entities/yyy.md`
- **更新页面**: `wiki/concepts/zzz.md`, `wiki/overview.md`
- **关键发现**: 一句话总结最重要的新知识
- **后续**: 此材料引发的新问题
```

---

### QUERY（回答问题）

触发条件：用户提问、说"分析"、"对比"、"解释"等。

**步骤：**

1. 阅读 `wiki/index.md` 识别相关页面
2. 阅读相关页面（通常 3-8 个）
3. 综合回答，**明确标注页面来源**（格式：`[[wiki/concepts/xxx]]`）
4. 最后询问用户：**"这个分析值得归档到 wiki 吗？"**
5. 用户确认后，保存到 `wiki/queries/YYYY-MM-DD-slug.md` 并更新索引

---

### LINT（健康检查）

触发条件："lint"、"检查 wiki"、"健康检查"等。

**检查项：**

- [ ] 孤立页面（没有入链）
- [ ] 损坏的链接（`[[link]]` 指向不存在的文件）
- [ ] 矛盾内容（不同页面的描述冲突）
- [ ] 过时信息（旧结论被新材料推翻）
- [ ] 提到但缺少专门页面的重要概念
- [ ] 缺少 `index.md` 中的页面
- [ ] 前置元数据不完整的页面

输出格式：列表，每项附带修复建议和严重级别 🔴 / 🟡 / 🟢。

---

## 链接约定

- 内部链接必须使用 Obsidian wikilink 格式（带 `wiki/` 前缀）：
  - 实体：`[[wiki/entities/geoffrey-hinton|Geoffrey Hinton]]`
  - 概念：`[[wiki/concepts/attention-mechanism|注意力机制]]`
  - 源摘要：`[[wiki/sources/hinton-2006-paper|论文标题]]`
- 外部链接使用标准 Markdown：`[text](https://url)`
- **每个页面至少应有 2 个出站内部链接**
- **高价值实体/概念页面应有 3 个或更多入链**

> 注意：Obsidian Vault 根目录是项目根目录（不是 `wiki/` 子目录），所以链接路径必须包含 `wiki/` 前缀才能正确解析。

---

## 内容质量标准

1. **精确优于全面** — 宁可少写也不写错
2. **标记矛盾** — 新材料与现有页面冲突时，保留两种说法并标注来源
3. **保留不确定性** — 使用"根据[来源]"而非绝对断言
4. **避免重复** — 每条信息只在最合适的页面上展开；从其他页面链接
5. **可操作** — 概念页面应包含"用例"或"进一步阅读"

---

## 会话开始清单

每次新会话开始时执行：

```
1. 读取 wiki/index.md  — 了解知识库当前状态
2. 读取 wiki/log.md 最后 10 条记录  — 了解近期活动
3. 确认用户意图（导入 / 查询 / 检查 / 其他）
4. 执行相应的工作流程
```

> `LLM.md` 由 LLM Agent 自动加载 — 无需手动操作。

---

## 禁止操作

- 不要修改 `raw/` 下的任何文件
- 不要删除 `wiki/log.md` 中的任何历史条目
- 不要在没有源材料支持的情况下断言事实（不要编造）
- 不要跳过更新 `index.md`
- 不要创建没有前置元数据的 wiki 页面
