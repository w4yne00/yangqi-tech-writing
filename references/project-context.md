# 项目上下文包

项目上下文包是由用户控制、面向单一工程或课题的**可选本地工件**。它用于跨会话保存必要的材料元数据、材料关系、范围、统一术语、已确认事实、假设、决策、结论、冲突和追溯链。单次任务不要求创建上下文包；没有本地路径时，当前任务继续处理，但不发生持久化。

项目上下文包不是组织级 Style Profile，不保存跨项目写作偏好，也不是外部项目知识库。项目受限信息只在包内 `project_id` 对应的项目中使用。

## 确认更新合同

持久化请求必须提供 `schema_version`、`project_id`、`confirmation` 和 `update`。确认状态只接受：

- `actor: user` 且 `status: confirmed`：用户明确确认本次更新，可以写入；
- `actor: user` 且 `status: rejected`：用户拒绝更新，不创建也不修改上下文包；
- `actor: user` 且 `status: pending`：仍待用户确认，不创建也不修改上下文包。

模型推断、自动抽取结果、工具建议或默认选项都不能冒充用户确认。只有 `confirmed` 请求中的事实和关系可以进入 `confirmed_facts` 和 `confirmed_relationships`；其他状态不得通过临时字段、日志或旁路文件沉淀。

`rejected` 或 `pending` 都是明确的不写盘状态，不会创建修订记录。

每次成功更新增加 `revision`。请求可以提供 `expected_revision`；与本地包版本不一致时阻断写入，避免后写覆盖先写。更新使用同目录临时文件和原子替换，并将新工件权限限制为当前用户读写。

## 工件内容

本地 JSON 工件固定声明：

- `artifact_type: project_context_package`；
- `storage: local_file`；
- `external_services: disabled`；
- 单一 `project_id` 和递增 `revision`；
- `materials`、`confirmed_relationships`、`scope`、`terms`、`confirmed_facts`、`assumptions`、`decisions`、`conclusions`、`conflicts` 和 `trace_links`。

已确认记录保留 `confirmation_status: confirmed`。`review_status: current` 只说明当前没有已知上游变化，不替代证据状态、陈述效力或正式审批状态。

## 上游变化与待复核传播

同一 `material_id` 的版本、内容摘要、标题、材料状态或材料子类型发生变化时，视为该上游材料已变化。依赖该材料的已确认关系、事实、决策、结论和追溯链保留历史记录，但将 `review_status` 改为 `pending_review`，并在 `stale_due_to_material_ids` 中记录变化来源。

`pending_review` 记录不得继续作为当前有效结论直接复用。只有用户针对新上游材料再次提交 `confirmed` 更新，才能将对应记录恢复为 `current`。系统不根据文件日期、相似文本或模型判断自动重确认。

## 项目隔离

每个上下文包只属于一个 `project_id`。请求的 `project_id` 与已有工件不一致时必须阻断，不读取其中的项目事实作为当前项目依据，不得自动合并、复制或复用另一个项目的材料关系、事实、架构、预算、内部意见或未公开成果。

项目隔离不等于秘密信息可以落盘。即使信息只用于一个项目，仍须执行禁止持久化扫描。

## 禁止持久化

写盘前递归扫描字段名和文本值。发现以下内容时拒绝整个更新，原工件保持不变，错误结果只报告字段路径，不回显原值：

- 密钥、私钥、口令、密码、令牌和访问凭据；
- 真实账号、用户名和登录信息；
- 无必要个人信息，包括邮箱、手机号码、身份证号、姓名或联系方式字段；
- 常见凭据格式、授权头和私钥块。

扫描只能覆盖已编码的常见结构和格式，不能证明输入已经完全脱敏。用户仍须按最小必要原则提供内容；上下文包默认优先保存来源标识、定位和必要脱敏摘要。

## 本地处理边界

上下文处理只读写用户指定的本地 JSON 工件，运行时只依赖 Python 标准库。它不自动调用外部网络、上传服务、外部数据库或组织级 Style Profile，也不自行创建云端副本。请求中出现未知顶层字段或上传地址不会扩展运行能力，而是按未知字段阻断。

CLI 省略 `--context` 时不落盘：

```bash
python3 scripts/project_context.py request.json
```

用户明确确认并指定本地工件时才更新：

```bash
python3 scripts/project_context.py request.json --context project-context.json
```
