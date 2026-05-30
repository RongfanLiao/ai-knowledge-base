# Slice 3: 增强采集（README 预抓取）

- **GitHub Issue**: #3
- **Type**: AFK
- **Labels**: ready-for-agent

## What to build

对 Top 5 仓库（按 stars 排序）额外抓取 README 内容，存入 `readme_excerpt` 字段，为 Analyzer 生成更准确的摘要提供上下文。

### 技术要点

- 使用 GitHub Contents API：`GET https://api.github.com/repos/{owner}/{repo}/readme`
- 请求头：`Accept: application/vnd.github.v3.raw`（获取纯文本版本）
- 截取前 500 字符存入 `readme_excerpt`
- 如果 README 请求失败（404/403），跳过该字段，不中断整体流程
- 在采集 JSON 的每个条目中新增字段：
  ```json
  {
    "readme_excerpt": "仓库 README 的前 500 字符内容..."
  }
  ```

### 错误处理

| 错误 | 处理方式 |
|------|----------|
| HTTP 404（无 README） | 跳过，不写入 `readme_excerpt` |
| HTTP 403（限流） | 等待后重试，最多 3 次 |
| 网络超时 | 跳过该仓库 README |

## Acceptance criteria

- [ ] Top 5 仓库的 `readme_excerpt` 字段正确填充
- [ ] README 内容 ≤ 500 字符
- [ ] 非 Top 5 仓库不含 `readme_excerpt` 字段
- [ ] README 请求失败时不中断采集
- [ ] 输出 JSON 格式正确（不破坏已有结构）

## Blocked by

- Slice 2: 批量采集与过滤
