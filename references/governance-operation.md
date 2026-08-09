# 治理运行域识别覆盖

本层用于在进入七类文种场景前识别制度制定、发布执行、检查评估、应急处置和修订材料。它只提供识别覆盖，并在明确的局部任务中加载既有场景基础合同；不新增治理材料专用深度规则，不推断组织职责或制度效力，也不补造制度依据、审批关系、处置权限或生效状态。

## 识别目录

| 生命周期位置 | 材料子类型 | 明确信号示例 | 文种场景 |
|---|---|---|---|
| `policy_development` | `management_policy` | 管理制度 | `security_policy` |
| `policy_development` | `management_measures` | 管理办法 | `security_policy` |
| `publication_execution` | `operating_procedure` | 操作规程 | `security_policy` |
| `emergency_response` | `emergency_plan` | 应急预案 | `security_policy` |
| `emergency_response` | `emergency_drill_plan` | 应急演练方案、演练方案 | `security_policy` |
| `emergency_response` | `special_response_plan` | 专项处置方案 | `security_policy` |
| `inspection_evaluation` | `governance_report` | 治理运行汇报、治理汇报 | `presentation` |
| `inspection_evaluation` | `governance_review_material` | 治理评审材料、制度评审材料 | `review_acceptance` |
| `revision` | `policy_revision` | 制度修订说明、制度修订材料 | `security_policy` |

该目录保留正交维度：治理汇报的业务域仍为 `governance_operation`，生命周期位置为 `inspection_evaluation`，文种场景为 `presentation`；治理评审材料使用 `review_acceptance`。制度正文、操作规程和应急预案可以共享安全制度基础场景，但材料子类型和生命周期位置不得互换。

## 近失配与降级

- 当前材料标题优先确定主材料身份。正文仅以“依据、引用、参照、参考、根据、按照、基于、见”等关系提及治理材料时，不把当前材料改判为被引用材料。
- 只出现“治理运行材料”等上位名称时，业务域、生命周期、文种和材料子类型保持 `unknown`、`unclear` 和带依据候选，进入 `conservative_audit`。
- 信息不足时只加载保护项、证据、陈述效力和 H1—H6 共性合同；不因“管理”“治理”“应急”等泛称直接补造责任主体、制度依据、审批权限、处置时限或生效状态。
- 管理制度、管理办法、操作规程、应急预案、演练方案和专项处置方案使用 `security_policy` 基础场景；治理汇报和治理评审材料分别保留汇报、评审验收文种场景。

## 正式强度与支持边界

- 规范性表述继续受保护项、陈述效力策略和 H3 约束。职责主体、应/不得、处置时限、报告对象、审批关系、分级条件、制度依据和附件表单不得因改写被新增、删除、强化或弱化。
- 材料身份明确、任务为局部 `rewrite`、`review` 或 `annotation` 时，加载对应七类场景基础合同并声明 `basic_support`。
- 已识别治理材料的整份 `create` 只声明 `recognition_coverage`，先进入写作准备单，不因材料名称已识别而生成不存在的组织职责、制度效力、管理要求或正式结论。
- 本层不声明 `deep_support`、`joint_review_support` 或 `forward_validation`。后续支持升级仍须满足材料合同与样本证据门槛。
