# 材料合同与样本证据登记

本合同供 Skill 维护者登记未来的正式要求、脱敏正例、失败案例、生命周期边界、缺失信息案例和联审案例。它只管理材料合同的证据来源与支持级别，不保存材料正文，不从合成案例推演行业规则，也不改变普通写作任务的执行链。

可复制模板位于 [`templates/material-contract-evidence-bundle.json`](../templates/material-contract-evidence-bundle.json)，使用以下标准库入口校验：

```bash
python3 scripts/material_contract_registry.py material-contract-evidence-bundle.json
```

入口只读取并校验 JSON，不写文件、不调用外部网络、不上传样本。校验成功返回 `validation.status: valid`、合同身份、支持级别、可计入证据的案例类型计数以及被排除的样本编号；校验失败返回退出码 `1` 和不回显敏感值的 JSON 错误。

## 登记包

顶层固定字段如下：

| 字段 | 要求 |
|---|---|
| `schema_version` | 当前为 `1.0` |
| `artifact_type` | 固定为 `material_contract_evidence_bundle` |
| `contract` | 一份材料合同定义 |
| `samples` | 与该合同关联的样本元数据数组；不放材料正文 |

未知字段会被拒绝，避免拼写错误或未约定数据静默进入登记。

## 材料合同模板

`contract` 必须完整记录：

- `contract_id`：合同稳定标识；
- `applicable_identity`：适用的业务域、生命周期位置、文种场景和材料子类型；
- `required_inputs`：所需输入、用途说明和是否必需；
- `content_responsibilities`：本材料必须承担的内容责任；
- `reasonable_depth`：本生命周期位置的合理深度及上下游边界；
- `statement_force`：允许的陈述效力与禁止的效力跃迁；
- `traceability`：要求、设计、承诺、实施、结论和证据之间应建立的追溯关系；
- `common_failures`：来自真实退回或审查的常见失败；
- `missing_information_handling`：缺失信息触发的占位、待确认、降级或阻断动作；
- `validation_case_ids`：用于当前支持级别声明的样本编号；
- `support_level`：`recognition_coverage`、`basic_support`、`deep_support`、`joint_review_support` 或 `forward_validation`。

模板只定义统一载体，不等于已经形成任何具体材料的深度合同。正式模板继续控制章节、编号、表格和必填项；材料合同只控制内容责任及证据边界。

## 样本入口

每个 `samples[]` 项必须记录以下元数据：

| 字段 | 要求 |
|---|---|
| `sample_id` | 登记包内唯一编号 |
| `source` | `source_id`、`source_type` 和可复核 `locator` |
| `authorization` | 授权状态 `status` 和授权用途 `scope` |
| `redaction_status` | `redacted`、`not_required`、`pending` 或 `failed` |
| `material_version` | 被评审材料或正式要求的版本 |
| `review_status` | `approved`、`pending` 或 `rejected` |
| `case_type` | 正式要求、正例、失败例、生命周期边界、缺失信息或联审/前向案例类型 |
| `data_classification` | `public`、`deidentified_reusable`、`project_restricted` 或 `prohibited_persistence` |
| `intended_uses` | `private_review`、`generic_rule`、`public_eval`、`capability_evidence` 的明确组合 |
| `evidence_type` | 正式要求、脱敏真实案例或确定性合成夹具的证据类型 |
| `model_execution` | 布尔值，明确是否实际执行模型 |

`source_type` 使用 `formal_requirement`、`real_case` 或 `synthetic_case`。正式要求必须配对 `case_type: formal_requirement` 和 `evidence_type: formal-requirement`；脱敏真实案例必须使用 `evidence_type: deidentified-real-case`，且不能冒充正式要求。

合成案例必须使用 `evidence_type: deterministic-synthetic-fixture` 并显式记录 `model_execution`。合成案例只验证确定性数据合同和边界，不计入正式要求或真实案例数量，也不代表模型通过率。

## 数据边界

- `authorization.status` 只有 `authorized` 或 `public_reuse` 时，样本才能进入可复用用途；`restricted` 和 `unknown` 只能保留为私有审阅登记。
- `project_restricted` 样本只能登记为 `private_review`，不能进入 `generic_rule`、`public_eval` 或 `capability_evidence`。
- 真实案例在进入通用规则、公开评测或能力证据前，必须获得授权、完成脱敏并通过评审。
- `prohibited_persistence` 会直接触发 `persistence_rejected_sensitive_data` 阻断。
- 即使分类字段填写错误，常见密钥、口令、令牌、真实账号和无必要个人信息仍会由禁止持久化扫描阻断；错误信息只列字段路径，不回显原值。
- 样本登记只保存元数据。需要私有审阅的项目受限材料仍在用户控制的项目环境中处理，不复制到本登记包。

## 支持级别与证据门槛

只有同时位于 `validation_case_ids`、用途包含 `capability_evidence`、授权有效、评审通过且数据可复用的样本，才计入能力声明。

| 支持级别 | 最低证据 |
|---|---|
| `recognition_coverage` | 能识别材料身份；不声明专用深度 |
| `basic_support` | 能加载基础场景、保护项、证据、陈述效力和质量合同 |
| `deep_support` | 1 项正式要求，以及正例、失败例、生命周期边界、缺失信息四类已授权脱敏真实案例 |
| `joint_review_support` | 满足深度支持，并增加追溯缺失、版本冲突、陈述效力不清和明确替代四类已授权脱敏真实案例 |
| `forward_validation` | 满足联审支持，并有 `case_type: forward_validation` 且 `model_execution: true` 的已审案例 |

缺少正式要求或任一所需真实案例时，`deep_support` 和 `joint_review_support` 声明会以 `unsupported_capability_claim` 阻断。当前仓库提供的模板和测试夹具不构成任何具体材料的深度支持、联审支持或前向验证证据。
