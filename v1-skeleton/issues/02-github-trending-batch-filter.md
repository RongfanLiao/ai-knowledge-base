# Slice 2: 批量采集与过滤

- **GitHub Issue**: #2
- **Type**: AFK
- **Labels**: ready-for-agent

## What to build

将采集从单条扩展到 Top 30 仓库，添加质量过滤规则，确保输出内容可靠。

### 过滤规则

- `stars >= 50`（过滤低质量仓库）
- 有英文 `description`（无描述的仓库通常质量较低）
- `fork: false`（排除 fork 仓库）
- 排除 awesome-list、课程作业、个人笔记等低信息密度项目
- 采集条数：15-30 条为正常范围；少于 10 条需扩展关键词；多于 50 条需收紧过滤

### 扩展字段

在 `items[]` 中额外添加：

| 字段 | 来源 | 说明 |
|------|------|------|
| `forks` | `forks_count` | Fork 数 |
| `license` | `license.spdx_id` | 许可证，无许可证填 `N/A` |
| `open_issues` | `open_issues_count` | Open Issue 数 |

## Acceptance criteria

- [ ] 每次请求获取 30 条结果
- [ ] 过滤后条目数 ≥ 5，≤ 30
- [ ] 所有过滤条件（stars、description、fork）生效
- [ ] `forks`、`license`、`open_issues` 字段正确填充
- [ ] 不到 10 条时自动扩展关键词并输出警示
- [ ] JSON 文件 `count` 与实际 `items` 数组长度一致

## Blocked by

- Slice 1: GitHub Trending 基础采集端到端
