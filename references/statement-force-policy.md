# 陈述效力策略

陈述效力说明一项内容在管理和交付链条中以何种身份成立；证据状态说明该内容是否有来源、是否冲突。两者正交判断：`SUPPORTED` 只证明来源支持原陈述，不会把建议方案强化为已批复边界、合同承诺、实施事实或验收结论。

## 效力类型

| 标识 | 含义 | 保守表达 |
|---|---|---|
| `assumption` | 为继续分析而暂设、尚待验证的前提 | “假设……；需确认……” |
| `professional_judgment` | 有明确责任主体的专业分析或判断 | “经分析……；判断……” |
| `recommended_solution` | 尚未形成批准、签署或实施事实的建议方案 | “建议……；推荐……” |
| `approved_boundary` | 由明确批复材料限定的范围、目标或条件 | 按批复口径复现 |
| `contractual_commitment` | 由合同、任务书或正式响应形成的履约承诺 | 保留责任主体、强度和条件 |
| `implementation_fact` | 由实施记录等材料确认的已发生状态 | 按实施记录及材料时点表述 |
| `acceptance_conclusion` | 由有权主体形成的评审或验收结论 | 保留结论主体、层级和限定语 |

`unknown` 只表示输入不足，不能作为定稿效力。系统必须输出待确认项，在确认前将可继续讨论的内容降为 `assumption`；若证据状态同时为 `NEEDS_USER_CONFIRMATION`，阻断自动定稿。

## 与证据状态联合决策

- `SUPPORTED`：保留来源陈述的原效力；来源存在不改变效力类型。
- `OPINION`：保留假设、专业判断或建议方案的责任属性，不伪装为正式事实；若同时标为已批复边界、合同承诺、实施事实或验收结论，阻断并确认元数据。
- `UNSUPPORTED`：不得改变效力来规避证据缺口；已批复边界、合同承诺、实施事实或验收结论缺少来源时阻断定稿。
- `CONTRADICTED`：阻断该陈述，不以降级、升格或文种转换替代冲突处理。
- `NEEDS_USER_CONFIRMATION`：保留待确认项；效力本身不明时采用更低效力表达。

## 文种转换边界

汇报压缩、会议纪要整理、投标应答、评审或验收写作都不能替换陈述效力。建议方案不能因转为汇报结论而成为 `approved_boundary`，已批复边界不能因改成方案说明而弱化为 `recommended_solution`；`contractual_commitment`、`implementation_fact` 和 `acceptance_conclusion` 也不得相互替代。

目标文种请求的效力与来源效力不一致时，输出 `preserve_source_force`，并以来源效力作为 `allowed_statement_force`。证据冲突时 `allowed_statement_force` 为空并输出 `block_conflict`。

## 风险与因果边界

陈述效力不覆盖[证据策略](evidence-policy.md)中的因果外推规则。上游进度偏差仍只能形成下游风险判断；没有同一对象的计划基线和可比较材料时点，不得写成下游事项的 `implementation_fact`，更不得据此形成 `acceptance_conclusion`。
