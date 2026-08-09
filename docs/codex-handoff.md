# Codex Handoff

## Versions and directories

- Stable: `v1.1.0` at repository root and installed Skill.
- Audit baseline: `outputs/yangqi-tech-writing-v1.1.0-rc.1/`.
- Previous candidate: `v1.1.0-rc.2`, preserved as the forward-test baseline.
- Release candidate: `v1.1.0-rc.3`, preserved in `work/` and `outputs/` as the verified release source.

## rc.3 scope

Fix FWD-01 causal extrapolation: an upstream schedule deviation must not be rewritten as a downstream completed delay fact without the downstream object's own plan baseline and comparable as-of time.

Post-review correction: the composite route now requires the downstream object to have both an explicit plan baseline and a comparable as-of time, unless the input directly confirms delay or a formal source states the delay conclusion. Dynamic forward-test status is not stored in the static-fixture result.

## Prohibited changes

Do not rewrite the seven scene packs, expand style vocabularies, add Style Profile or Distiller integration, add runtime dependencies, modify rc.1, or replace the installed Skill.

## Required verification

Run the complete unittest suite, three CLI smoke tests, product and forward JSON parsers, skill-creator quick validation, link checks, version checks, privacy scans and independent outputs-directory verification.

## Evidence boundary

The 8-case comparison is a deterministic static fixture with 16 assertions. The rc.3 forward retest used three fresh-context single runs and passed 9/9 frozen assertions plus human review. Neither result proves statistical stability.

## Foundation 11 scope

Issue #12 adds a maintainer-facing material-contract and sample-evidence registry. The distributed template records applicable identity, required inputs, content responsibilities, reasonable depth, statement force, traceability, common failures, missing-information handling, validation cases and support level. Sample metadata records source, authorization, redaction, material version, review status, case type, data classification, intended uses, `evidence_type` and `model_execution`.

Project-restricted samples are limited to private review. Prohibited-persistence data is rejected. Synthetic cases never count as formal requirements or real cases. Deep, joint-review and forward-validation claims are blocked unless their declared evidence gate is complete. The template itself remains at `basic_support` and does not claim a deep material contract.

Foundation 11 verification on 2026-07-30 passed 134 root unit tests, including 19 material-contract registry behavior tests. Post-review corrections require intended uses to stay within the explicit authorization scope, keep pending or rejected samples out of reusable uses, structure and validate statement-force transitions, keep the synthetic fixture at `basic_support`, and test that forward evidence requires recorded model execution.

## Foundation 10 scope

Issue #11 extends the highest-level perception seam with a richer material normalized view, formal-template adaptation and extraction-gap blocking. The view can preserve source filename, title/clause/table/figure hierarchy, page/table/figure locators, table relations, citation locations and extraction gaps while remaining a derived, non-formal input.

Formal templates control chapters, numbering, tables and required items; material contracts only check content responsibilities. Without a formal template, the decision returns an explicitly suggested, non-formal and adjustable outline. OCR uncertainty, lost table relationships and unrecoverable figures block only explicitly dependent high-risk claims; low-risk dependencies are recorded without broadening the blocker.

Foundation 10 verification on 2026-08-09 passed 194 root unit tests, including seven new highest-level behavior tests and one reference-contract test. Post-review regressions preserve an existing evidence-conflict action alongside the independent extraction-gap action and prevent complete-create or material-set routing from overriding an extraction-gap blocker with `two_stage`. The three CLI smoke tests returned 2/2/0, four product and two existing forward JSON files parsed, root quick validation passed, and the preserved rc.3 outputs copy independently passed its 66 tests, quick validation and four product JSON parsers. The core still uses only the Python standard library and does not implement DOCX, PDF, Excel, OCR or image parsers. The old outputs candidate was verified read-only and was not replaced.

## Foundation 12 scope

Issue #13 adds one maintainer-facing deterministic synthetic benchmark over the existing public perception and project-context seams. Its 26 cases cover the three business domains, seven document scenes, lifecycle near misses, composite materials, statement-force preservation, quick/two-stage processing, material relations, conflict blocking, confirmed context updates, project isolation, formal-template adaptation, extraction-gap blocking and prohibited-persistence boundaries.

Foundation 12 verification on 2026-08-09 passed 202 root unit tests, including seven unified benchmark integration tests and one reference-contract test. The benchmark directly reruns the existing eval immutability, trigger accuracy, audit behavior and stable contract test modules, in addition to checking the 43 behavior evals, 20 trigger boundaries, three audit-script exit contracts and stable `1.1.0` metadata. The preserved rc.3 outputs copy independently passed 66 tests, Skill validation and four product JSON parsers. Every benchmark case is deterministic synthetic input with `model_execution: false` and is non-real engineering evidence. It supports only recognition coverage and basic support claims; it does not establish deep support, joint-review support, forward validation or statistical stability. No stable release was published, the installed Skill was not replaced, and no GitHub Release was created.

## Issue #1 closure scope

The umbrella specification was reviewed against the cumulative Foundation 01–12 implementation using `v1.1.0` as the fixed point. Three remaining public-contract gaps were closed: formal templates can carry explicit semantic responsibility mappings without requiring title equality or inferring completeness from a recommended outline; recognized complete-create and material-set tasks retain a writing preparation sheet when extraction gaps force `conservative_audit`; and the perception request now exposes and enforces an unknown-field policy, with schema objects rejecting unknown fields, locator objects remaining extensible, and task scope limited to `document` or `local`.

Issue #1 closure verification on 2026-08-09 passed 205 root unit tests, Python bytecode compilation, the three CLI smoke contracts with expected exits `2/2/0`, five product JSON parsers, the material-contract template validator and root Skill validation. The preserved rc.3 outputs copy remained read-only and independently passed its 66 tests, Skill validation and four product JSON parsers. No deep support, joint-review support, forward-validation or statistical-stability claim was added; the stable version, installed Skill and preserved outputs candidates were not replaced.

## Release status

The FWD-01, unfinished-without-baseline and explicit-overdue forward cases passed, and the clean outputs copy passed independent verification. The candidate was released as stable v1.1.0 after 66 local tests passed.

## Git and publication

The user authorized stable integration, local Skill replacement, commit and GitHub push on 2026-07-12. Creating a GitHub Release remains a separate action unless explicitly requested.

## 中文交接摘要

- rc.3 已在证据、汇报、复合路由和 H6 四层增加因果外推边界，行为评测增至 43 项。
- 审计修正已收紧复合路由的逻辑连接词，并增加语义合同与跨文档状态一致性测试。
- 真实前向复测中，FWD-01、无计划基线和明确逾期 3 个全新上下文案例已通过 9/9 条冻结断言及人工审稿；原始输出和评分已保留。
- rc.3 已集成为稳定版 v1.1.0；根目录与安装副本的发布验证均以 66 项测试为准。
- 前向案例每项只运行 1 次，不得包装为统计稳定性证明。
- Foundation 11 已建立材料合同与脱敏样本登记入口；合成夹具保持 `basic_support`，不作为深度或联审能力证据，根目录回归为 134 项。
- Foundation 10 已扩展材料标准化视图并增加正式模板适配与提取缺口阻断；正式模板控制结构，无模板时只给建议提纲，三类提取缺口仅阻断显式依赖的高风险结论，根目录回归为 194 项。
- Foundation 12 已建立 26 案例统一确定性合成证据基准，根目录回归为 202 项；全部案例属于非真实工程证据，只支持识别覆盖和基础支持声明，不构成深度支持、联审支持、前向验证或统计稳定性证明。
- 本次已授权提交、推送和覆盖安装；GitHub Release 仍需单独授权。
