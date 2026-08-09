# 科研课题域识别覆盖

本层用于在进入七类文种场景前识别科研课题材料的生命周期位置和材料子类型。它只提供识别覆盖，并在明确的局部任务中加载既有场景基础合同；不新增科研材料专用深度规则，不推断主管部门制度，也不补造科研管理要求。

## 识别目录

| 生命周期位置 | 材料子类型 | 明确信号示例 | 文种场景 |
|---|---|---|---|
| `application` | `research_application` | 科研申报书、科研课题申报书、课题申报书 | `feasibility_study` |
| `application` | `research_feasibility_assessment` | 科研课题可行性论证、可研论证及其报告 | `feasibility_study` |
| `task_agreement` | `research_task_agreement` | 科研课题任务书、课题任务书 | `technical_spec` |
| `research_implementation` | `research_implementation_plan` | 科研实施方案、研究实施方案、科研课题研究实施方案 | `architecture_design` |
| `midterm_review` | `research_interim_report` | 科研课题中期汇报 | `presentation` |
| `midterm_review` | `research_interim_inspection` | 科研课题中期检查及其报告 | `review_acceptance` |
| `final_acceptance` | `research_final_acceptance` | 科研课题结题验收材料、结题验收报告 | `review_acceptance` |
| `final_acceptance` | `research_final_acceptance_presentation` | 科研课题结题验收汇报、科研结题验收汇报 | 主 `presentation`＋局部 `review_acceptance` |

该目录保留正交维度：科研中期汇报的生命周期位置为 `midterm_review`，文种场景仍为 `presentation`；中期检查处于同一科研生命周期位置，但使用 `review_acceptance`。科研结题验收与工程验收可以共享评审验收基础场景，但业务域、生命周期和材料子类型不得互换；结题验收汇报以 `presentation` 为主场景，并在验收结论等局部内容加载 `review_acceptance`。

## 近失配与降级

- “工程实施方案”识别为工程建设实施位置；“研究实施方案”识别为科研课题研究实施位置。只出现“实施方案”时同时保留工程和科研候选，不猜测业务域。
- “科研课题申报材料”“科研课题任务约定材料”“科研课题研究实施材料”等上位名称只形成对应生命周期和材料子类型候选，不直接确认具体文种。
- 只出现“科研课题中期材料”时，保留中期汇报与中期检查候选；只出现未明确“结题”的科研课题验收报告时，保留科研结题验收候选，不转成工程验收身份。
- 明确科研归属与“工程实施方案”等工程限定标题冲突时，同时保留工程与科研候选并进入保守审阅，不用跨字段子串覆盖工程限定词。
- 当前材料标题优先确定主材料身份。正文引用另一业务域的实施方案或成果，不覆盖明确标题；任务明确否定标题分类并给出替代材料时，可以修正分类。
- 任务或正文明确确认“材料属于科研课题”时，可以与标题中的“申报书”“可研论证”“任务书”“实施方案”“中期汇报”“中期检查”等泛称组合识别；缺少明确科研归属时，这些泛称本身不证明业务域。
- “依据、引用、参照、参考、根据、按照、基于、见”科研材料的表述只表示来源关系，不把当前材料改判为被引用材料。
- 只出现上位名称、信号冲突或材料类型被明确否定时，相关维度保持 `unknown`、`unclear` 和带依据候选，进入 `conservative_audit`，只加载共性保护、证据、陈述效力与 H1—H6 合同。
- “项目”“验收报告”“中期材料”等泛称不足以单独证明科研课题业务域。只有“结题验收”等科研生命周期信号或明确科研/课题归属时，才进入科研识别。

## 支持边界

- 材料身份明确、任务为局部 `rewrite`、`review` 或 `annotation` 时，加载对应七类场景基础合同并声明 `basic_support`。
- 已识别科研材料的整份 `create` 只声明 `recognition_coverage`，先进入写作准备单，不因材料名称已识别而生成主管要求、考核指标、固定章节、验收条件或正式结论。
- 本层不声明 `deep_support`、`joint_review_support` 或 `forward_validation`。后续支持升级仍须满足材料合同与样本证据门槛。
