# 正式模板适配与提取缺口阻断

本合同规定专业文档工具的提取结果如何进入核心处理链，以及正式模板和提取缺口如何约束后续写作。核心只处理结构化输入和可观察决策，不承担办公文件或图像解析。

## 材料标准化视图

材料标准化视图是来源材料的派生输入，不是新的正式材料，也不产生批准、签署、合同承诺、实施事实或验收结论效力。视图可以记录：

- `source_id`、`source_filename` 和 `material_status`；
- `structural_nodes`，用于保留标题、条款、表格和图示层级，以及父子关系；
- 页码、表号和图号等来源定位；
- `table_relations`，用于保留表头、单元格或其他表格语义关系；
- `citation_locations`，用于回到来源材料复核引文；
- `extraction_gaps`，用于记录提取类型、缺口位置、说明和受影响的 Claim。

`is_formal_material` 必须为 `false`。缺少可用来源定位时，请求无效；核心不得把标准化视图作为新的控制性材料。

## 正式模板适配

请求提供 `formal_template` 时，正式模板控制章节、编号、表格和必填项。输出使用 `structure_adaptation.mode: formal_template`，并保留模板标识、名称、来源和控制项。

材料合同只检查内容责任是否落实，不得以通用提纲替换正式模板，不得因标题不同直接认定内容缺失，也不得擅自新增、删除或重排正式章节。模板存在内容责任缺口时，先定位并报告，由用户确认处理方式。

请求未提供 `formal_template` 时，才允许输出 `recommended_outline`。该对象必须同时标记 `label: 建议提纲`、`status: suggested`、`is_formal_template: false` 和 `adjustable: true`，说明其来源是已解析的材料或场景合同，不得包装为主管要求、组织标准或正式格式。

## 提取缺口阻断

支持以下提取缺口：

- `ocr_uncertain`：OCR 不确定；
- `table_relationship_lost`：表格关系丢失；
- `figure_unrecoverable`：图示无法恢复。

每个缺口通过 `affected_claim_ids` 声明影响范围。只有显式依赖该缺口且标记为 `risk: high` 的高风险结论被阻断；低风险或无依赖关系的 Claim 只记录缺口，不扩大阻断范围。风险等级与 `statement_force` 正交，不根据假设、专业判断、建议方案或正式效力名称反推风险，也不以效力较低为由忽略输入中明确标记的高风险。

被阻断的 Claim 在 `extraction_gap_action` 中使用 `block_extraction_gap`，不覆盖原有证据或陈述效力处理动作，不产生允许陈述效力，并进入 `extraction_gap_review.blocked_claim_ids` 和顶层 `blockers`。处理模式降级为 `conservative_audit`，在重新提取、回看来源或获得可核验证据前不得定稿。

## 核心边界

核心不实现 DOCX、PDF、Excel、OCR 或图像解析器，不调用外部解析服务，也不新增运行时第三方依赖。`scripts/perception_decision.py` 继续仅使用 Python 标准库；专业提取、版面恢复和图像识别由边界外工具完成。

本合同只判断材料输入、结构控制和提取证据是否足以支撑写作，不判断技术方案正确性、法规适用性或模板本身是否符合主管要求。
