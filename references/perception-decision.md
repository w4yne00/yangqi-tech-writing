# 感知与处理决策合同

本合同是用户任务和材料标准化视图进入七类场景执行链之前的最高层接缝。它只形成可观察的路由决策，不替换场景包、保护项、证据策略或 H1—H6，也不判断技术正确性。

## 输入合同

请求包含 `task`、`material_view`、可选的 `claims` 和可选的 `material_set`：

- `task`：包含用户指令、任务模式和处理范围；任务模式使用 `create`、`continue`、`rewrite`、`review` 或 `annotation`。
- `material_view`：`schema_version` 为 `1.0`，`view_type` 为 `material_normalized_view`，并保留 `source_id`、`material_status`、标题及至少一个带 `locator` 的内容片段。
- `claims`：每项至少包含 `claim_id`、`text`、`evidence_status` 和 `statement_force`；文种转换请求改变表达身份时另给 `requested_statement_force`。
- `material_set`：记录材料集标识、上游材料完整性声明、材料清单、显式关系和冲突；字段及边界见[材料集追溯与冲突阻断](material-set-review.md)。
- `is_formal_material` 必须为 `false`。标准化视图是从来源材料提取的派生输入，不产生新的批准、签署、合同或验收效力。

当前最小定位可以是章节和页码，也可以是其他能够回到来源材料复核的非空定位对象。核心不解析 DOCX、PDF、表格、图片或 OCR。

`evidence_status` 使用 `SUPPORTED`、`OPINION`、`UNSUPPORTED`、`CONTRADICTED` 或 `NEEDS_USER_CONFIRMATION`；`SUPPORTED` 必须提供 `source_ref`。`statement_force` 使用 `assumption`、`professional_judgment`、`recommended_solution`、`approved_boundary`、`contractual_commitment`、`implementation_fact`、`acceptance_conclusion` 或 `unknown`。

## 输出合同

输出包含标准化视图的来源摘要和统一决策：

- 业务域、生命周期位置、文种场景和材料子类型均使用 `value`、`confidence`、`candidates` 三字段结构。
- 明确信号使用 `explicit`；信息不足时使用 `unknown` 值和 `unclear` 置信状态，并在候选项中记录依据。
- 任务模式保持用户授权，不因材料分类改变。
- 支持级别只声明 `recognition_coverage` 或 `basic_support`。最小切片不声明深度支持、联审支持或前向验证。
- 处理模式可以是 `quick_path`、`two_stage` 或 `conservative_audit`。已识别的完整方案新建和多材料整合使用 `two_stage`；材料身份明确、范围为 `local` 且没有待确认项或阻断项的局部改写、审阅和只标问题任务可以使用 `quick_path`。
- `two_stage` 输出 `writing_preparation_sheet`，包含材料清单与关系、感知维度、控制性材料、事实与判断、假设、冲突、待确认项、确认边界、追溯摘要和拟加载合同。完整字段和阶段边界见[写作准备单与快速通道](writing-preparation.md)。
- 快速通道仍执行保护项、证据、陈述效力和 H1—H6；局部任务一旦存在无来源高效力陈述、证据冲突、效力不明或其他待确认/阻断项，就降级为 `conservative_audit`。
- `claim_decisions` 逐项输出证据状态、来源效力、请求效力、允许效力和处理动作，保持证据状态与陈述效力正交。
- `material_set_review` 输出单材料或材料集模式、材料元数据、七类显式关系、控制依据、冲突、跨阶段可核验状态和完成声明。
- 材料集只按明确关系确定控制与替代线索，不按日期自动形成 `supersedes`；批准、签署、用户指定和 `governs` 可以作为可审查的控制依据。
- 范围、数量、参数、责任、时间、结论和陈述效力冲突，以及 `conflicts_with`、`unclear` 关系都会阻断自动定稿。冲突输出只呈现差异、影响和待确认项，不作效力裁决。
- 单材料模式和上游缺失的材料集均将跨阶段一致性标为 `not_verifiable`，完成声明保持 `not_completed`。
- 来源效力与请求效力不一致时使用 `preserve_source_force`；效力不明时使用 `confirm_and_use_lower_force` 并暂按 `assumption`；证据冲突时使用 `block_conflict` 且不产生允许效力；`OPINION` 与正式效力并存时使用 `confirm_evidence_force_alignment` 并阻断。
- 加载合同使用稳定的语义标识，不暴露内部目录扫描顺序。
- 待确认项列出阻止确定分类的维度；阻断项只记录不能继续自动处理的事项。

当前明确的初步设计审阅加载以下合同：

1. `common.protected_spans`
2. `common.evidence_policy`
3. `common.statement_force_policy`
4. `scene.architecture_design`
5. `common.quality_gate_h1_h6`

当前切片对明确、局部且边界清楚的初步设计 `rewrite`、`review` 或 `annotation` 声明基础支持并允许快速通道。明确初步设计、范围为 `document` 的 `create` 只声明识别覆盖并进入两阶段处理；材料子类型仍为 `unknown` 的普通文档新建保持保守审阅，不因 `document` 单一字段扩大两阶段范围。

提供 `material_set` 时固定进入 `two_stage`，加载 `common.material_set_review` 和 `common.writing_preparation`，先形成写作准备单。`reviewable` 只表示输入可进入人工联审，不表示已经获得联审支持、完成一致性验证或可以定稿。

缺少足够信号、信号被明确否定或相互冲突时，只加载共性保护、证据、陈述效力和质量合同，进入保守审阅；不得为了获得确定分类而补造业务域、生命周期或材料子类型。

## 调用

```bash
python3 scripts/perception_decision.py request.json
python3 scripts/perception_decision.py - < request.json
```

脚本仅依赖 Python 3.9 及以上标准库。请求不满足合同或把标准化视图标记为正式材料时，返回退出码 `1`，并在标准错误输出结构化的 `invalid_request`。
