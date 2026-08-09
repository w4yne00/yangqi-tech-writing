# 复合文种路由

复合材料不新增场景 ID。主文种决定整体语域、章节结构和默认档位；局部文种决定保护项、规范强度和删改权限。局部规则风险更高时，以局部规则为准。

统一感知决策在 `composite_routing` 中记录 `primary_scene`、`local_scene`、`effective_scope`、`effective_protection_boundary` 和 `protected_reason`。两个场景分别使用 `applies_to_content` 说明适用内容，并用 `protection_boundary` 声明保护边界；局部片段结束后恢复主文种规则。

主场景同时作为顶层 `document_scene`，局部场景不覆盖业务域、生命周期位置或材料子类型。局部场景的保护风险更高时，`effective_scope` 为 `local_scene_content`，`effective_protection_boundary` 采用局部边界，`protected_reason` 记录为 `local_scene_has_higher_risk`。

缺少专用材料合同时，`contract_resolution` 将 `dedicated_material_contract` 标记为 `unavailable`，并通过 `scene_base_contracts` 加载主、局部两个既有场景基础合同。明确的局部改写、审阅或只标问题声明 `basic_support`；新建、续写等其他模式保持 `recognition_coverage`，均不声明 `deep_support`。

## 统一感知案例

### 初步设计评审汇报

保留工程建设业务域和设计生命周期。`presentation` 是主场景，适用于整体语域、汇报结构和信息压缩；`review_acceptance` 是局部场景，适用于评审意见、评审结论、问题数量、整改责任和日期。主场景可使用 `structural`，局部内容使用更严格的 `in_place`。

### 科研课题结题验收汇报

保留科研课题业务域和结题验收生命周期。`presentation` 是主场景，适用于整体语域、汇报结构和信息压缩；`review_acceptance` 是局部场景，适用于验收结论、科研成果、考核指标、问题数量、整改责任和日期。局部内容同样使用更严格的 `in_place`。

## 四类组合

### 可研＋架构

可研决定论证语域；架构参数段使用 `in-place`，标准编号、系统名、RTO/RPO、拓扑和接口关系保持。

### 投标＋招标原文

投标应答决定输出结构；招标原文完全保护，只处理响应说明。无证明材料时不得补写“完全满足”。

### 汇报＋验收结论

汇报正文可使用 `structural`；引用的验收结论、问题数量、整改责任和日期使用 `in-place`。
不得跨对象转移计划状态：上游延期可以作为下游风险原因，但只有下游自身同时具备明确计划基线与可比较材料时点，或存在输入直接确认或正式延期结论时，才可写“下游已延期”。

### 制度＋会议纪要

制度条款保持规范强度；纪要中的人员或角色意见保持归属，不合并为统一结论。
