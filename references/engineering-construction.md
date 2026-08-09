# 工程建设域识别覆盖

本层用于在进入七类文种场景前识别工程建设材料的生命周期位置和材料子类型。它只提供识别覆盖，并在明确的局部任务中加载既有场景基础合同；不新增材料专用深度规则，也不判断技术方案是否正确。

## 识别目录

| 生命周期位置 | 材料子类型 | 明确信号示例 | 文种场景 |
|---|---|---|---|
| `initiation` | `project_proposal` | 项目建议书 | `feasibility_study` |
| `initiation` | `feasibility_study` | 工程可研报告、可行性研究报告 | `feasibility_study` |
| `design` | `preliminary_design` | 初步设计、初设 | `architecture_design` |
| `design` | `preliminary_design_review_presentation` | 初步设计评审汇报、初设评审汇报 | 主 `presentation`＋局部 `review_acceptance` |
| `design` | `detailed_design` | 详细设计、详设 | `architecture_design` |
| `design` | `overall_architecture` | 总体架构 | `architecture_design` |
| `procurement` | `technical_specification` | 技术规范书、招标或采购技术要求 | `technical_spec` |
| `procurement` | `bid_response` | 投标技术应答、投标应答 | `bid_response` |
| `implementation` | `engineering_implementation_plan` | 工程实施方案 | `architecture_design` |
| `implementation` | `implementation_record` | 工程实施记录 | `review_acceptance` |
| `implementation` | `stage_report` | 工程建设或项目实施阶段汇报 | `presentation` |
| `trial_run` | `trial_run_report` | 工程试运行报告 | `review_acceptance` |
| `acceptance` | `acceptance_outline` | 工程验收大纲 | `review_acceptance` |
| `acceptance` | `acceptance_report` | 工程验收报告 | `review_acceptance` |
| `operation` | `operation_report` | 工程运行维护或运营报告 | `presentation` |

该目录保留近失配边界：可研、初设、详设和总体架构是不同材料子类型；技术规范与投标应答分别表示采购要求和采购响应；验收大纲与验收报告分别表示验收策划和验收结果材料。

## 支持边界

- 材料身份明确、任务为局部 `rewrite`、`review` 或 `annotation` 时，加载对应七类场景基础合同并声明 `basic_support`。
- 已识别工程材料的整份 `create` 只声明 `recognition_coverage`，先进入写作准备单，不因名称已识别而补造专用章节、指标或正式要求。
- 只出现“工程立项材料”“设计材料”“工程采购材料”“工程实施材料”“工程试运行材料”“工程验收材料”“工程运营材料”等上位名称时，输出对应生命周期的候选子类型、可复核依据和待确认项，只加载共性保护、证据、陈述效力与 H1—H6 合同。
- 泛称“实施方案”“阶段汇报”不足以排除科研课题或治理运行语境，不直接认定为工程建设材料。
- 当前材料标题优先确定主材料身份，任务指令可以明确否定标题分类；正文中引用的上游、采购、验收材料或科研课题成果不覆盖主材料身份，但任务或正文明确给出的科研课题业务域仍会阻断工程域分类。
- “项目”本身不足以区分工程建设与科研课题；项目验收只能作为候选依据。肯定的“科研”或“课题”语境会阻断项目建议书、阶段汇报和验收材料的工程建设分类或候选；任务明确否定科研语境并给出工程文种时，以否定后的工程材料身份继续识别。
- 本层不声明 `deep_support`、`joint_review_support` 或 `forward_validation`。后续支持升级仍须满足材料合同与样本证据门槛。
