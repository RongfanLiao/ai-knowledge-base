# Slice 4: 分析与评分

- **GitHub Issue**: #4
- **Type**: AFK
- **Labels**: ready-for-agent

## What to build

实现 Analyzer Agent 的分析能力：读取 `knowledge/raw/github-trending-{date}.json` 中的每个条目，生成中文技术摘要、五维评分、提取标签，并将分析结果追加到条目中。

### 分析流程

#### 2.1 生成技术摘要

100-200 字的中文摘要，需包含：
- **这是什么**：核心内容（一句话）
- **为什么重要**：对 AI/LLM/Agent 从业者的实际价值
- **关键技术点**：核心架构/算法/技术
- **适用场景**：谁会用到

优先使用 `readme_excerpt` 作为上下文（如 Slice 3 已实现）；没有的话可使用 WebFetch 补充。

#### 2.2 五维评分

| 维度 | 权重 | 评分标准 |
|------|------|----------|
| 技术深度 | 0.25 | 底层原理、架构设计、算法创新 |
| 实用价值 | 0.30 | 工程师能否直接使用 |
| 时效性 | 0.20 | 反映最新趋势 |
| 社区热度 | 0.15 | Stars/Score 是否突出 |
| 领域匹配 | 0.10 | 与 AI/LLM/Agent 核心匹配度 |

**公式**: `relevance_score = tech_depth*0.25 + practical_value*0.30 + timeliness*0.20 + community_heat*0.15 + domain_match*0.10`

**豁免规则**: 如果 `tech_depth >= 0.85`，时效性自动满分（0.20）

#### 2.3 标签提取

3-5 个英文小写标签，如 `[agent-framework, multi-agent, python, openai]`

### 输出格式

每个条目新增字段：

```json
{
  "summary": "中文摘要...",
  "relevance_score": 0.87,
  "score_breakdown": {
    "tech_depth": 0.80,
    "practical_value": 0.95,
    "timeliness": 0.90,
    "community_heat": 0.85,
    "domain_match": 0.95
  },
  "tags": ["agent-framework", "multi-agent", "python"],
  "analyzed_at": "2026-05-31T11:00:00Z"
}
```

## Acceptance criteria

- [ ] 每个条目都有 `summary` 字段，100-200 字
- [ ] 摘要使用中文撰写，技术术语保留英文
- [ ] `relevance_score` 范围 0.00-1.00，保留两位小数
- [ ] `score_breakdown` 包含全部 5 个维度
- [ ] `tags` 包含 3-5 个标签
- [ ] `analyzed_at` 时间戳正确
- [ ] 不丢失原始采集字段（追加而非覆盖）
- [ ] 低于 0.6 的条目仍保留分析结果

## Blocked by

- Slice 2: 批量采集与过滤
