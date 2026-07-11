# Testing

验证日期：2026-07-11

## Environment

- 本地验证：Python 3.9.6
- CI 矩阵：Python 3.9、3.11、3.12
- 测试依赖：PyYAML 6.0.3，仅用于解析 `SKILL.md` frontmatter
- 技能运行时：Python 3.9 标准库，无第三方依赖

## Commands

在仓库根目录执行：

```bash
python3 -m unittest discover -s tests -v
python3 scripts/protected_diff.py tests/fixtures/before.md tests/fixtures/after.md
python3 scripts/evidence_check.py tests/fixtures/evidence-ledger.json
python3 scripts/style_audit.py tests/fixtures/sample.md
jq empty evals/evals.json
```

安装了本地 `skill-creator` 时，还可执行：

```bash
python3 /Users/wayne/.agents/skills/skill-creator/scripts/quick_validate.py .
```

## Results

- 仓库单元测试：27 项通过，0 失败，0 错误，0 跳过。
- 其中技能结构与行为测试 22 项，发布元数据、CI 合同与脱敏回归测试 5 项。
- Skill 结构校验：通过，输出 `Skill is valid!`。
- 保护项烟测：按预期退出 `2`，检出 `2026年8月15日`、`承建方` 和“负责”强度缺失。
- 证据账本烟测：按预期退出 `2`，高风险 `UNSUPPORTED` Claim `C-SMOKE-001` 进入阻断项。
- 风格审计烟测：按预期退出 `0`，检出 3 个 T1 软提示；`authorship_verdict` 为 `not_applicable`。
- 评测数据：24 项、七类正式场景全覆盖，另含近失配和 Annotation mode；每项含 2—3 个可核验断言。
- 首次设计阶段的内联烟测覆盖案例 1、5、16、24，共 12 条断言全部满足；因无基线，该结果只作为非盲 smoke evaluation。

## CI

`.github/workflows/test.yml` 在 push 和 pull request 时使用 Python 3.9、3.11、3.12 运行全量测试和风格审计烟测。CI 安装 PyYAML 仅为测试 frontmatter，三个运行时脚本仍只依赖标准库。

## Known limitations

- 正则脚本只能发现已编码的表面差异，不能确定技术方案是否正确。
- 脚本不能判断法规、标准或制度对具体项目的法律适用性。
- 风格命中不构成 AI 作者身份判断，也不应作为作者检测结论。
- 保护项脚本不能发现全部隐含责任、复杂表格关系、图示拓扑和同义术语漂移，仍需人工保真复读。
- 证据检查依赖人工建立 Claim 账本，不能自动穷尽正文中的全部客观主张。
