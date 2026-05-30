# Slice 5: 整理归档与去重

- **GitHub Issue**: #5
- **Type**: AFK
- **Labels**: ready-for-agent

## What to build

实现 Organizer Agent 的整理归档能力：读取已分析的原始数据 → 质量过滤 → 去重 → 格式化 → 写入知识条目文件 → 更新索引。

### 流程

#### 1. 验证必填字段

```
id, title, url, summary, relevance_score, tags, analyzed_at
```

缺失任何一个 → 标记 `incomplete` 并写入过滤日志。

#### 2. 质量过滤

| 条件 | 动作 |
|------|------|
| `relevance_score < 0.6` | 丢弃，记入 `filtered-{date}.json` |
| `summary` < 50 字 | 丢弃 |
| `tags` < 2 个 | 丢弃 |
| `url` 格式异常 | 丢弃 |

#### 3. 去重

对比 `knowledge/articles/index.json`：
- 精确匹配 `url` → 跳过
- 模糊匹配 `title` > 90% → 跳过
- 同时读取 `filtered-*.json` 中已丢弃条目的 `url`，避免重复处理

#### 4. ID 生成

`kb-{YYYY-MM-DD}-{三位序号}`，当天所有数据源统一递增。

#### 5. 写入文件

每个条目 → `knowledge/articles/{YYYY-MM-DD}-{slug}.json`

同时更新 `knowledge/articles/index.json`：
- `last_updated` 时间戳
- `total_count` 总数
- `entries` 新增条目

### 过滤日志格式

```json
{
  "date": "2026-05-31",
  "source": "github-trending",
  "filtered_at": "2026-05-31T11:30:00Z",
  "total_discarded": 5,
  "items": [
    { "id": "...", "title": "...", "reason": "relevance_score 0.42 < 0.6" }
  ]
}
```

## Acceptance criteria

- [ ] 所有输出条目 `relevance_score >= 0.6`
- [ ] 无重复条目（`url` 唯一）
- [ ] 每个条目 `id` 唯一且符合命名规则
- [ ] `index.json` `total_count` 与实际文章数一致
- [ ] 过滤日志记录了每条丢弃的 `id` 和原因
- [ ] 全流程完成后不丢失原始采集文件

## Blocked by

- Slice 4: 分析与评分
