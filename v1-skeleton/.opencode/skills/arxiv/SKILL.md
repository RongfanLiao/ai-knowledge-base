---
name: arxiv
description: When you need to collect AI/LLM/Agent related papers from arXiv
---

# arXiv 论文采集技能

## 触发场景

当用户要求从 arXiv 采集 AI/LLM/Agent 相关的最新论文时，自动激活此技能。

## 采集步骤

### 1. 构造查询请求

使用 arXiv API 搜索最近 24 小时内提交的论文：

```
GET http://export.arxiv.org/api/query
```

**查询参数**：
- `search_query`: 组合以下分类（OR 连接）：
  - `cat:cs.AI` — 人工智能
  - `cat:cs.LG` — 机器学习
  - `cat:cs.CL` — 计算语言学与自然语言处理
  - `cat:cs.MA` — 多智能体系统
  - `cat:cs.IR` — 信息检索（含 RAG 相关）
- `sortBy`: `submittedDate`
- `sortOrder`: `descending`
- `max_results`: `30`
- `start`: `0`

**完整请求示例**：
```
http://export.arxiv.org/api/query?search_query=cat:cs.AI+OR+cat:cs.LG+OR+cat:cs.CL+OR+cat:cs.MA+OR+cat:cs.IR&sortBy=submittedDate&sortOrder=descending&max_results=30
```

### 2. 解析与过滤

arXiv 返回 Atom XML，需解析以下字段：

| 字段 | XML 路径 | 说明 |
|------|----------|------|
| `id` | `entry/id` | arXiv ID，如 `http://arxiv.org/abs/2501.00001v1` |
| `title` | `entry/title` | 论文标题 |
| `summary` | `entry/summary` | 论文摘要 |
| `url` | `entry/id` | 将 ID 转为 `https://arxiv.org/abs/{id}` 格式 |
| `authors` | `entry/author/name` | 作者列表 |
| `categories` | `entry/category[@term]` | arXiv 分类标签 |
| `published` | `entry/published` | 提交日期 |
| `updated` | `entry/updated` | 更新日期 |
| `comment` | `entry/arxiv:comment` | 作者备注（如页码、项目链接） |
| `link_pdf` | `entry/link[@title="pdf"]/@href` | PDF 下载链接 |

**过滤条件**（采集后应用）：
- 标题或摘要命中以下关键词之一：`LLM`, `large language model`, `agent`, `multi-agent`, `RAG`, `retrieval augmented`, `fine-tuning`, `instruction tuning`, `RLHF`, `reasoning`, `chain-of-thought`, `tool use`, `MCP`, `function calling`
- 排除以下类型：勘误、撤稿通知、会议日程、卷首语
- 英文论文优先（非英文摘要需额外标注）

### 3. 提取元数据

对每个通过过滤的论文，提取以下信息：

```json
{
  "id": "{arxiv_id}",
  "title": "{论文标题（去除换行）}",
  "summary": "{论文摘要（去除换行）}",
  "url": "https://arxiv.org/abs/{id}",
  "pdf_url": "https://arxiv.org/pdf/{id}",
  "authors": ["{author1}", "{author2}"],
  "categories": ["cs.AI", "cs.LG"],
  "published": "{published date}",
  "updated": "{updated date}",
  "comment": "{author comment if any}"
}
```

### 4. 限流策略

| 限制 | 处理方式 |
|------|----------|
| 请求频率 | 每 10 秒最多 1 次请求（arXiv 官方建议），超限会返回 HTTP 503 |
| 单次最大结果 | `max_results` 上限 100，超过会被截断 |
| 重试 | HTTP 503 时等待 30 秒后重试，最多 3 次 |
| 超时 | 网络超时设为 15 秒 |

### 5. 输出

将采集结果保存为 JSON 文件：

- 文件路径：`knowledge/raw/arxiv-{YYYY-MM-DD}.json`
- 顶层包含 `source`, `collected_at`, `query`, `count`, `items`
- 使用 2 空格缩进

```json
{
  "source": "arxiv",
  "collected_at": "2026-05-29T10:30:00Z",
  "query": "cat:cs.AI OR cat:cs.LG OR cat:cs.CL, sorted by submittedDate, max 30",
  "count": 15,
  "items": [
    {
      "id": "2501.00001v1",
      "title": "A New Approach to LLM Reasoning...",
      "url": "https://arxiv.org/abs/2501.00001v1",
      "summary": "We propose a novel method...",
      "authors": ["Author A", "Author B"],
      "categories": ["cs.AI", "cs.LG"],
      "published": "2026-05-29T00:00:00Z",
      "updated": "2026-05-29T12:00:00Z"
    }
  ]
}
```

## 质量标准

- 采集条目数：10-30 条为正常范围
- 少于 5 条：关键词或分类可能过窄，报告给用户
- 多于 50 条：需要收紧过滤条件
- 所有 `id` 必须唯一（arXiv 允许多个版本，取最新版本即可）
