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

Foundation 11 verification on 2026-07-30 passed 133 root unit tests, including 18 material-contract registry behavior tests. Post-review corrections require intended uses to stay within the explicit authorization scope, keep pending or rejected samples out of reusable uses, structure and validate statement-force transitions, and keep the synthetic fixture at `basic_support`.

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
- Foundation 11 已建立材料合同与脱敏样本登记入口；合成夹具保持 `basic_support`，不作为深度或联审能力证据，根目录回归为 133 项。
- 本次已授权提交、推送和覆盖安装；GitHub Release 仍需单独授权。
