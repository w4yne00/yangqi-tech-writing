# 感知与处理决策合同

本合同是用户任务和材料标准化视图进入七类场景执行链之前的最高层接缝。它只形成可观察的路由决策，不替换场景包、保护项、证据策略或 H1—H6，也不判断技术正确性。

## 输入合同

请求包含 `task`、`material_view`、可选的 `formal_template`、可选的 `claims` 和可选的 `material_set`：

- `task`：包含用户指令、任务模式和处理范围；任务模式使用 `create`、`continue`、`rewrite`、`review` 或 `annotation`，处理范围只能使用 `document` 或 `local`。
- `material_view`：`schema_version` 为 `1.0`，`view_type` 为 `material_normalized_view`，并保留 `source_id`、`material_status`、标题及至少一个带 `locator` 的内容片段；需要时通过 `source_filename`、`structural_nodes`、`table_relations`、`citation_locations` 和 `extraction_gaps` 保留文件名、标题条款层级、页表图定位、表格关系、引用位置和提取缺口。
- `formal_template`：记录模板标识、名称、来源，以及模板控制的章节、编号、表格和必填项；省略时表示当前请求没有提供正式模板。
- `claims`：每项至少包含 `claim_id`、`text`、`evidence_status` 和 `statement_force`；文种转换请求改变表达身份时另给 `requested_statement_force`，提取缺口阻断使用 `risk` 的 `low`、`medium` 或 `high`，省略时按 `medium` 处理。
- `material_set`：记录材料集标识、上游材料完整性声明、材料清单、显式关系和冲突；字段及边界见[材料集追溯与冲突阻断](material-set-review.md)。
- `is_formal_material` 必须为 `false`。标准化视图是从来源材料提取的派生输入，不产生新的批准、签署、合同或验收效力。

当前最小定位可以是章节和页码，也可以是其他能够回到来源材料复核的非空定位对象。标题、条款、表格和图示使用 `structural_nodes` 保留父子层级；表格语义关系和引用位置分别使用 `table_relations` 和 `citation_locations`。完整字段和边界见[正式模板适配与提取缺口阻断](formal-template-adaptation.md)。核心不解析 DOCX、PDF、表格、图片或 OCR。

`evidence_status` 使用 `SUPPORTED`、`OPINION`、`UNSUPPORTED`、`CONTRADICTED` 或 `NEEDS_USER_CONFIRMATION`；`SUPPORTED` 必须提供 `source_ref`。`statement_force` 使用 `assumption`、`professional_judgment`、`recommended_solution`、`approved_boundary`、`contractual_commitment`、`implementation_fact`、`acceptance_conclusion` 或 `unknown`。

未知字段策略如下：请求、任务、材料标准化视图、Claim、正式模板及材料集等 schema 对象采用 `reject_unknown_fields`，出现未声明字段时返回 `invalid_request`，避免拼写错误或未来字段被静默丢弃。`locator` 是专业提取工具的扩展边界，采用 `allow_extension_fields`，但仍必须至少包含一个可用定位值。输出通过顶层 `unknown_field_policy` 公开这两项策略。

## 输出合同

输出包含标准化视图的来源摘要和统一决策：

- 业务域、生命周期位置、文种场景和材料子类型均使用 `value`、`confidence`、`candidates` 三字段结构。
- 明确信号使用 `explicit`；信息不足时使用 `unknown` 值和 `unclear` 置信状态，并在候选项中记录依据。
- 主材料身份按材料标题、任务指令、正文片段的顺序识别；正文引用的其他材料名称或科研课题成果不覆盖明确标题，任务指令中的明确否定可以拒绝标题分类，明确给出的替代类型可以修正标题。材料身份优先级不覆盖业务域约束，任务或正文明确给出的科研课题归属语境仍会阻断工程域分类。
- 工程建设候选须与已知业务域信息一致；肯定的“科研”或“课题”语境不产生工程建设分类或候选，任务已明确否定的科研语境不再阻断其后明确给出的工程文种；被任务明确否定的材料子类型也不保留在候选列表中。
- 科研课题识别须保留科研生命周期与既有文种场景两个正交维度；科研中期汇报不能丢失 `midterm_review` 或 `presentation`，结题验收不能替换为工程建设 `acceptance` 身份。
- 明确科研课题归属可以与另一输入字段中的申报书、可研论证、任务书、实施方案、中期汇报或中期检查泛称组合识别；“依据、引用、参照、参考、根据、按照、基于、见”科研材料只表示来源关系，不形成当前材料身份。
- 治理运行识别须保留治理生命周期与既有文种场景两个正交维度；治理汇报不能丢失 `governance_operation`、`inspection_evaluation` 或 `presentation`，制度正文、操作规程和应急预案不得合并为同一材料子类型。
- 复合材料在顶层 `document_scene` 保留主场景，并通过 `composite_routing` 同时输出主、局部场景各自的适用内容和保护边界。局部规则风险更高时，局部内容采用更严格边界，不把整个材料压成单一场景。
- 初步设计评审汇报保留 `engineering_construction`、`design` 和 `presentation` 主场景，评审意见与结论加载 `review_acceptance` 局部场景；科研课题结题验收汇报保留 `research_project`、`final_acceptance` 和相同的主/局部场景关系。
- 复合材料缺少专用材料合同时，`contract_resolution` 明确降级到 `scene_base_contracts`；支持级别仍按任务模式保持 `recognition_coverage` 或 `basic_support`，不声明 `deep_support`。
- 正文仅以“依据、引用、参照、参考、根据、按照、基于、见”等关系提及治理材料时，不形成当前材料身份；信息不足时不推断组织职责、审批权限或制度效力。
- 任务模式保持用户授权，不因材料分类改变。
- 支持级别只声明 `recognition_coverage` 或 `basic_support`。最小切片不声明深度支持、联审支持或前向验证。
- 处理模式可以是 `quick_path`、`two_stage` 或 `conservative_audit`。已识别的完整方案新建和多材料整合使用 `two_stage`；材料身份明确、范围为 `local` 且没有待确认项或阻断项的局部改写、审阅和只标问题任务可以使用 `quick_path`。
- `two_stage` 输出 `writing_preparation_sheet`，包含材料清单与关系、感知维度、控制性材料、事实与判断、假设、冲突、待确认项、确认边界、追溯摘要和拟加载合同。完整新建或多材料整合因高风险提取缺口降级为 `conservative_audit` 时仍保留准备单，但下一阶段固定为先消解阻断。完整字段和阶段边界见[写作准备单与快速通道](writing-preparation.md)。
- 快速通道仍执行保护项、证据、陈述效力和 H1—H6；局部任务一旦存在无来源高效力陈述、证据冲突、效力不明或其他待确认/阻断项，就降级为 `conservative_audit`。
- `claim_decisions` 逐项输出证据状态、来源效力、请求效力、允许效力和处理动作，保持证据状态与陈述效力正交。
- `structure_adaptation` 明确结构控制权。提供正式模板时使用 `formal_template` 模式，模板控制章节、编号、表格和必填项，`semantic_responsibility_mapping` 只记录用户或正式来源显式提供的责任到模板控制项映射，且不得输出推荐提纲；映射不要求标题相同。没有经验证的专用材料合同责任集时只标记 `provided_unverified` 或 `needs_confirmation`，不声称映射完整，也不把推荐提纲当作材料合同责任。未提供正式模板时使用 `recommended_outline` 模式，提纲必须标记为 `suggested`、可调整且不是正式模板。
- `extraction_gap_review` 逐项记录 OCR 不确定、表格关系丢失或图示无法恢复的影响范围。缺口显式关联到 `risk: high` 的 Claim 时，Claim 在独立的 `extraction_gap_action` 中使用 `block_extraction_gap`，保留原有证据处理动作，不产生允许陈述效力并进入阻断项；低风险或未声明依赖关系时只记录缺口。
- `material_set_review` 输出单材料或材料集模式、材料元数据、七类显式关系、控制依据、冲突、跨阶段可核验状态和完成声明。
- 材料集只按明确关系确定控制与替代线索，不按日期自动形成 `supersedes`；批准、签署、用户指定和 `governs` 可以作为可审查的控制依据。
- 范围、数量、参数、责任、时间、结论和陈述效力冲突，以及 `conflicts_with`、`unclear` 关系都会阻断自动定稿。冲突输出只呈现差异、影响和待确认项，不作效力裁决。
- 单材料模式和上游缺失的材料集均将跨阶段一致性标为 `not_verifiable`，完成声明保持 `not_completed`。
- 来源效力与请求效力不一致时使用 `preserve_source_force`；效力不明时使用 `confirm_and_use_lower_force` 并暂按 `assumption`；证据冲突时使用 `block_conflict` 且不产生允许效力；`OPINION` 与正式效力并存时使用 `confirm_evidence_force_alignment` 并阻断。
- 加载合同使用稳定的语义标识，不暴露内部目录扫描顺序。
- 待确认项列出阻止确定分类的维度；阻断项只记录不能继续自动处理的事项。

明确工程建设材料的局部审阅加载以下合同：

1. `common.protected_spans`
2. `common.evidence_policy`
3. `common.statement_force_policy`
4. 与材料文种对应的一个既有 `scene.*` 场景合同；复合材料再加载局部场景基础合同
5. `common.quality_gate_h1_h6`

工程建设识别目录覆盖立项、设计、采购、实施、试运行、验收和运营位置，并区分项目建议书、可研、初设、详设、总体架构、技术规范、投标应答、工程实施方案、实施记录、阶段汇报、试运行报告、验收大纲、验收报告和运行维护报告。只有上位阶段名称时，各生命周期位置均返回带依据的候选，不直接确认材料子类型。完整目录及近失配边界见[工程建设域识别覆盖](engineering-construction.md)。

科研课题识别目录覆盖申报、任务约定、研究实施、中期检查和结题验收位置，并区分申报书、可研论证、任务书、研究实施方案、中期汇报、中期检查与结题验收材料。未限定业务域的“实施方案”同时保留工程与科研候选；明确信号则加载对应既有场景基础合同。完整目录及支持边界见[科研课题域识别覆盖](research-project.md)。

治理运行识别目录覆盖制度制定、发布执行、检查评估、应急处置和修订位置，并区分管理制度、管理办法、操作规程、应急预案、演练方案、专项处置方案、治理汇报、治理评审和制度修订材料。制度类材料加载 `security_policy` 基础场景，治理汇报和评审材料分别保留 `presentation` 与 `review_acceptance` 场景。完整目录及支持边界见[治理运行域识别覆盖](governance-operation.md)。

材料身份明确、局部且边界清楚的工程建设、科研课题或治理运行 `rewrite`、`review` 或 `annotation` 声明基础支持并允许快速通道。已识别材料、范围为 `document` 的 `create` 只声明识别覆盖并进入两阶段处理；材料子类型仍为 `unknown` 的普通文档新建保持保守审阅，不因 `document` 单一字段扩大两阶段范围，也不补造科研管理要求、组织职责或制度效力。

提供 `material_set` 时固定进入 `two_stage`，加载 `common.material_set_review` 和 `common.writing_preparation`，先形成写作准备单。`reviewable` 只表示输入可进入人工联审，不表示已经获得联审支持、完成一致性验证或可以定稿。

缺少足够信号、信号被明确否定或相互冲突时，只加载共性保护、证据、陈述效力和质量合同，进入保守审阅；不得为了获得确定分类而补造业务域、生命周期或材料子类型。

## 调用

```bash
python3 scripts/perception_decision.py request.json
python3 scripts/perception_decision.py - < request.json
```

脚本仅依赖 Python 3.9 及以上标准库。请求不满足合同或把标准化视图标记为正式材料时，返回退出码 `1`，并在标准错误输出结构化的 `invalid_request`。
