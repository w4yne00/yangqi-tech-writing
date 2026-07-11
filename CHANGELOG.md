# Changelog

本项目遵循 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/) 的组织方式，并采用 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

## [Unreleased]

当前没有尚未发布的变更。

## [1.0.0] - 2026-07-11

### Added

- 建立 G 企网络安全与信息化技术材料的起草、审阅和保真改写流程。
- 支持可研立项、架构设计、技术规范、投标应答、安全制度与预案、汇报材料、评审验收七类场景。
- 建立 protected spans、证据账本、T1/T2/T3 风格审计、改写档位、scope 和 H1—H6 质量闸门。
- 提供 `protected_diff.py`、`evidence_check.py`、`style_audit.py` 三个 Python 标准库脚本。
- 提供 24 项评测数据，覆盖应修改、不应修改、硬闸门、近失配和 Annotation mode。

### Quality

- 提供 22 项技能行为与结构测试，以及 5 项公开发布元数据、CI 合同与脱敏回归测试。
- 对保护项丢失和高风险无来源 Claim 使用非零退出码阻断。
- 风格审计明确返回 `authorship_verdict: not_applicable`，不作作者身份判断。

### Known Limitations

- 正则脚本不能确定技术方案是否正确。
- 本项目不能判断法规、标准或制度对具体项目的法律适用性。
- 风格命中不构成 AI 作者身份判断。

[Unreleased]: https://github.com/w4yne00/yangqi-tech-writing/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/w4yne00/yangqi-tech-writing/releases/tag/v1.0.0
