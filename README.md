# yangqi-tech-writing

[![Tests](https://github.com/w4yne00/yangqi-tech-writing/actions/workflows/test.yml/badge.svg)](https://github.com/w4yne00/yangqi-tech-writing/actions/workflows/test.yml)
[![Version](https://img.shields.io/badge/version-v1.1.0-blue.svg)](VERSION)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

G 企网络安全与信息化技术材料的起草、审阅和保真改写 Skill。

*A writing, review, and fidelity-preserving rewriting skill for cybersecurity and IT documents in Chinese state-owned enterprises.*

当前稳定版本：`v1.1.0`

v1.1.0 增强保护项、证据检查、复合文种路由和 Annotation mode，并增加跨对象计划状态的因果外推边界。上游事项延期只能支持下游风险判断；下游“已延期”须同时具备自身计划基线与可比较材料时点，或由输入、正式来源直接确认。

## 项目定位

`yangqi-tech-writing` 用于降低 G 企技术材料中的模板感、表演性语言和信息空转，同时保护法规标准、数字参数、技术术语、责任主体、规范性强度和正式结论。

它不是通用“洗稿”工具，也不以口语化替代正式表达。项目不判断作者身份，不保证技术方案正确或法律适用，也不会为增强论证而编造数字、事故、案例、认证和效果。

## 七类场景

| 场景 | 典型材料 | 默认策略 |
|---|---|---|
| 可研立项 | 可研、项目建议书、建设必要性、投资效益 | `standard / bounded` |
| 架构设计 | 初设、详设、总体架构、部署与接口设计 | `minimal或standard / in-place` |
| 技术规范 | 技术规范书、招标需求、评分条款 | `minimal / in-place` |
| 投标应答 | 逐条响应、偏离说明、证明材料 | `minimal或standard / in-place` |
| 安全制度 | 管理制度、操作规程、应急预案 | `minimal / in-place` |
| 汇报材料 | 领导汇报、PPT 文字稿、一页纸 | `standard / structural` |
| 评审验收 | 评审意见、验收报告、会议纪要 | `minimal / in-place` |

## 核心执行链路

```text
识别场景
  → 锁定保护项
  → 检查证据状态
  → 保持陈述效力
  → 识别 T1/T2/T3 风格问题
  → 选择改写档位与 scope
  → 起草、审阅或改写
  → 两遍复读
  → H1—H6 质量闸门
```

四项硬原则：

- 事实不漂移；
- 术语不替换；
- 责任不模糊；
- 正式度不降低。

H1—H6 分别检查保护项、证据状态、规范强度、场景合同、用户授权和结论追溯。任一硬闸门失败，不输出“可定稿、可签批、完全响应或通过验收”的结论。

## 安装

### 使用 Release 安装包

从 [Releases](https://github.com/w4yne00/yangqi-tech-writing/releases) 下载 `yangqi-tech-writing.skill`，按所用 Agent 或 Codex 客户端的 Skill 安装方式导入。

### 从源码安装

```bash
git clone https://github.com/w4yne00/yangqi-tech-writing.git
mkdir -p "$CODEX_HOME/skills"
mkdir -p "$CODEX_HOME/skills/yangqi-tech-writing"
cp yangqi-tech-writing/SKILL.md "$CODEX_HOME/skills/yangqi-tech-writing/"
cp -R yangqi-tech-writing/references yangqi-tech-writing/scripts "$CODEX_HOME/skills/yangqi-tech-writing/"
```

重启或重新加载 Skill 列表后，确认 `yangqi-tech-writing` 可用。

## 使用示例

### 可研报告改写

```text
按 G 企可研报告风格改写这段建设必要性。保留政策文号、投资金额、
建设周期和现状事实；没有来源的数据列为待确认项。
```

### 技术规范审阅

```text
审阅这份技术规范。保持条款编号和所有“应、须、不得”，只标出不可验证、
主体不明或缺少验收方法的要求，不要自行补参数。
```

### Annotation mode

```text
先别改稿，只列出最主要的五个问题。每项包含定位、问题类型、影响、风险级别、
建议动作和是否建议改写；没有实质问题时明确说明无需调整。
```

完整执行规则见 [SKILL.md](SKILL.md)，场景边界见 [references/scene-packs](references/scene-packs)。

## 感知决策接缝

`scripts/perception_decision.py` 接收“用户任务＋材料标准化视图＋可选陈述＋可选材料集”的 JSON 请求，输出统一的业务域、生命周期位置、文种场景、材料子类型、任务模式、陈述效力边界、材料关系、支持级别、处理模式、加载合同、待确认项和阻断项。陈述的证据状态与效力分别记录；有来源的建议不会变成已批复或已实施事实，文种转换也不能在已批复边界、合同承诺、实施事实和验收结论之间替换。

材料集关系支持 `governs`、`derives_from`、`supersedes`、`implements`、`verifies`、`conflicts_with` 和 `unclear`。控制与替代只采用批准、签署、用户指定或明确关系，不按文件日期自动覆盖；范围、数量、参数、责任、时间、结论和陈述效力冲突形成阻断项。单材料或上游缺失时会明确标记无法验证跨阶段一致性，不声称联审完成。该兼容切片不表示任何材料组合已经获得联审支持。

材料标准化视图必须保留 `source_id`、材料状态和至少一个原文定位，并明确标记 `is_formal_material: false`。它是专业文档工具生成的派生输入，不是新的正式材料。输入不足时，决策保留 `unknown`、`unclear` 及带依据的候选分类。

```bash
python3 scripts/perception_decision.py request.json
```

## 项目上下文包

持续性工程或课题可以选择维护项目隔离的本地 JSON 上下文包，用于保存材料元数据、已确认关系、范围、术语、已确认事实、假设、决策、冲突和追溯链。单次任务不需要上下文包；省略 `--context` 时不会落盘。

只有请求明确提供 `confirmation.status: confirmed` 和 `confirmation.actor: user` 时才写入。`rejected` 或 `pending` 保持本地文件不变；同一上游材料发生版本或内容变化时，关联结论、决策、关系和追溯链进入 `pending_review`。已有上下文包的 `project_id` 与请求不一致时阻断，项目受限信息不会自动跨项目合并或复用。

写盘前会拒绝常见密钥、口令、令牌、真实账号和无必要个人信息，错误结果不回显原值。该入口只使用 Python 标准库和用户指定的本地 JSON 文件，不自动调用外部网络、上传服务或外部数据库。完整合同见 [项目上下文包](references/project-context.md)。

```bash
python3 scripts/project_context.py request.json
python3 scripts/project_context.py request.json --context project-context.json
```

## 目录结构

```text
yangqi-tech-writing/
├── SKILL.md                 # 运行入口与场景路由
├── references/              # 共性规则和七类场景包
├── scripts/                 # 感知决策、项目上下文与三个确定性审计脚本
├── tests/                   # 单元测试与烟测样例
├── evals/evals.json         # 43 项行为评测
├── TESTING.md               # 验证记录和局限
├── CHANGELOG.md             # 版本变更
├── ROADMAP.md               # 后续路线
└── VERSION                  # 当前版本号
```

## 审计脚本

三个既有审计脚本只使用 Python 标准库，输出 JSON，入口和退出码保持不变。

### 保护项差异

```bash
python3 scripts/protected_diff.py before.md after.md
```

- `0`：已编码保护项和规范性词数量未发现差异；
- `1`：输入或读取错误；
- `2`：保护项缺失或规范性强度发生变化。

### 证据账本

```bash
python3 scripts/evidence_check.py evidence-ledger.json
```

- `0`：账本通过；
- `1`：JSON 或 schema 错误；
- `2`：存在高风险 `UNSUPPORTED`、`CONTRADICTED` 或待确认阻断项。

### 风格审计

```bash
python3 scripts/style_audit.py document.md
```

脚本以 `0` 返回 T1/T2/T3 软提示。命中不是自动修改指令，更不是 AI 作者检测结果。

## 测试

```bash
python3 -m unittest discover -s tests -v
python3 scripts/style_audit.py tests/fixtures/sample.md
```

GitHub Actions 在 Python 3.9、3.11 和 3.12 上运行测试。详细结果和已知局限见 [TESTING.md](TESTING.md)。

## 版本策略

项目采用 Semantic Versioning：

- `v1.0.0`：七类场景、24 项评测和三个审计脚本；
- `v1.1.0`：43 项行为评测、复合文种路由、增强保护项与证据检查，以及因果外推边界；
- `v1.1.x`：兼容的规则、评测和脚本增强；
- `v1.2.0`：组织级 Style Profile 加载接口；
- `v2.0.0`：与独立 `yangqi-style-distiller` 建立稳定协议。

具体方向见 [ROADMAP.md](ROADMAP.md)，已发布变更见 [CHANGELOG.md](CHANGELOG.md)。

## 贡献

欢迎通过 Issue 提供脱敏后的失败案例、误报案例和场景边界问题。Pull Request 应说明修改原因，补充相应测试，并确保原有保护项、证据和质量闸门不被弱化。

请勿提交真实账号、密钥、未脱敏内部材料、受限政策文件或未经授权的客户文档。

## 能力边界与免责声明

- 正则脚本只能发现已编码的表面差异，不能确定技术方案是否正确。
- 本项目不能判断法规、标准或制度对具体项目的法律适用性。
- 风格审计不判断作者身份，也不构成 AI 检测结论。
- 保护项和证据检查不能代替技术评审、法务审查、采购审查和人工签批。

## License

本项目采用 [MIT License](LICENSE)。
