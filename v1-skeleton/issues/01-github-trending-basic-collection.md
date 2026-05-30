# Slice 1: GitHub Trending 基础采集端到端

- **Type**: AFK
- **Labels**: ready-for-agent

## What to build

实现 Collector Agent 的 GitHub Trending 基础采集能力。通过 GitHub Search API 搜索 AI/LLM/Agent 相关仓库，单条端到端验证：调用 API → 解析响应 → 提取关键字段 → 写入知识库原始数据文件。

### 技术要点

- 使用 `GET https://api.github.com/search/repositories`
- 查询关键词：`AI OR LLM OR agent OR "large language model" OR RAG OR MCP`
- 排序方式：`sort=stars&order=desc`
- 时间窗口：`created:>{7天前}`
- per_page: 1（本 Issue 先验证单条成功）
- 请求头：`Accept: application/vnd.github.v3+json`, `Authorization: Bearer ${GITHUB_TOKEN}`
- 输出文件：`knowledge/raw/github-trending-{YYYY-MM-DD}.json`

### 提取字段

| 字段 | 来源 |
|------|------|
| `id` | `full_name` |
| `title` | `name` |
| `description` | `description` |
| `url` | `html_url` |
| `stars` | `stargazers_count` |
| `language` | `language` |
| `topics` | `topics` |
| `created_at` | `created_at` |
| `updated_at` | `pushed_at` |

### 输出 JSON 结构

```json
{
  "source": "github-trending",
  "collected_at": "2026-05-31T10:00:00Z",
  "query": "AI OR LLM OR agent, past 7 days, sorted by stars",
  "count": 1,
  "items": [...]
}
```

## Acceptance criteria

- [ ] 成功调用 GitHub Search API 并返回有效响应
- [ ] 正确提取仓库的 `id`, `title`, `url`, `stars`, `language`, `topics`, `created_at`, `updated_at`
- [ ] 写入 `knowledge/raw/github-trending-{YYYY-MM-DD}.json`，JSON 格式正确（2 空格缩进，UTF-8）
- [ ] `collected_at` 时间戳正确，ISO 8601 格式
- [ ] 幂等性：重复运行同一天不覆盖已存在文件

## Blocked by

None - can start immediately
