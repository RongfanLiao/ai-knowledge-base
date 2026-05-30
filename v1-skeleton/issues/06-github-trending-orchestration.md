# Slice 6: 全自动编排流水线

- **Type**: HITL
- **Labels**: ready-for-human

## What to build

设计并实现 GitHub Trending 的端到端编排流水线：一个命令/脚本即可触发 Collector → Analyzer → Organizer 的完整流程，并确保幂等性。

### 需要设计的架构决策

1. **编排方式**：使用 OpenCode 的多 Agent 委派（`@collector` → `@analyzer` → `@organizer`），还是编写外部编排脚本（Shell/Python）？

2. **身份注入**：`GITHUB_TOKEN` 如何从 `.env` 文件安全传递到 Collector Agent 的请求头？

3. **状态传递**：Analyzer 是直接修改 raw JSON 文件，还是通过对话传递分析结果给主 Agent？当前 Analyzer 设计为不使用 Write 工具，分析结果通过对话返回。

4. **幂等性保障**：
   - Collector：当天文件已存在时追加去重
   - Analyzer：已有 `analyzed_at` 字段的条目不再重复分析
   - Organizer：`index.json` 增量更新

5. **错误传播**：Collector 失败时是否继续执行 Analyzer？各阶段的错误如何处理？

### 输出要求

- 一份编排脚本（Shell 或 Python），放在项目根目录
- 更新 AGENTS.md 中关于流水线调用的章节
- 支持通过简单命令一键触发：`./pipeline.sh github-trending` 或类似

### 质量要求

- 重复运行同一天不产生重复条目
- 任一阶段失败时，记录清晰的错误信息
- 支持指定日期参数（默认今天）

## Acceptance criteria

- [ ] 一个命令即可触发完整的 GitHub Trending 采集→分析→归档流程
- [ ] 幂等性验证：重复运行第 2 次不产生重复条目
- [ ] `.env` 文件中的 `GITHUB_TOKEN` 被安全使用
- [ ] 任一阶段失败有清晰的错误日志
- [ ] AGENTS.md 中更新了流水线调用说明

## Blocked by

- Slice 3: 增强采集（README 预抓取）
- Slice 5: 整理归档与去重
