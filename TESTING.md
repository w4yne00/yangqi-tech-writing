# Testing

验证日期：2026-07-12；稳定版本：`1.1.0`。

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
python3 -m unittest tests.test_perception_decision -v
python3 -m json.tool evals/evals.json
python3 -m json.tool evals/trigger-evals.json
python3 -m json.tool evals/trigger-results.json
python3 -m json.tool evals/static-fixture-results.json
```

安装了本地 `skill-creator` 时，还可执行：

```bash
python3 "$HOME/.agents/skills/skill-creator/scripts/quick_validate.py" .
```

## Results

- Foundation 01 当前根目录完整单元测试为 76 项通过、0 项失败；三个既有审计脚本烟测、产品 JSON 解析和 Skill 结构校验继续符合原合同。
- Foundation 01 新增 2 个最高层感知决策案例和 10 项外部行为测试：明确的初步设计审阅输出完整决策，信息不足或材料类型被否定时保留 `unknown`、`unclear` 和候选分类，非审阅任务不扩大支持声明，最小定位可由任一有效片段提供。
- 新增案例标记为 `deterministic-synthetic-fixture`，`model_execution` 为 `false`；它只验证确定性决策合同和测试数据一致性，不代表真实模型运行通过率。
- 材料标准化视图回显来源标识、材料状态和最小定位，并固定声明为派生视图而非正式材料。
- v1.1.0 稳定版根目录在集成后完成全量单元测试：66 项通过、0 项失败，达到至少 45 项的验收门槛；rc.3 的 work 与干净 outputs 副本此前亦分别通过 66 项测试。
- Skill 结构校验实际返回 `Skill is valid!`，退出码为 `0`；frontmatter 继续仅含 `name`、`description`。
- 本地安装副本已使用 v1.1.0 的 `SKILL.md`、`references/` 和 `scripts/` 覆盖，并通过结构校验及逐目录一致性比较。
- 保护项烟测：按预期退出 `2`，检出 `2026年8月15日`、`承建方` 和“负责”强度缺失。
- 重复保护项回归：同一标准编号由两次降为一次时实际退出 `2`，`missing_counts.standard_id` 为 `1`；两次保持两次时实际退出 `0`。
- 证据账本烟测：按预期退出 `2`，高风险 `UNSUPPORTED` Claim `C-SMOKE-001` 进入阻断项。
- 风格审计烟测：按预期退出 `0`，检出 3 个 T1 软提示；`authorship_verdict` 为 `not_applicable`。
- 评测数据：43 项行为案例和 20 项触发边界查询；前 40 项与 rc.2 快照逐项相同，新增 3 项因果外推边界案例。
- 触发边界：候选 20/20，基线 19/20；修复 1 项非目标写作任务误触发，高风险正例无回退。
- 8 组确定性规则夹具、16 条静态断言全部通过。该结果验证规则覆盖和测试数据一致性，不代表模型运行通过率。
- rc.3 真实前向复测：3 个 `fork_turns=none` 全新上下文用例通过 9/9 条预先冻结断言，人工审稿 3 项均通过。
- FWD-01 已关闭：上游网络策略调整晚12天被写为“可能影响问题2后续整改进度”，没有再写成问题2已延期；无基线案例不判定延期，明确逾期案例保持“已逾期”。
- 语义合同回归明确检查“计划基线与材料时点同时成立”的布尔关系，并拒绝旧的宽松连接词；跨文档状态回归确保静态夹具不再保存动态前向门禁。
- 每个前向 prompt 仅运行 1 次；模型标识、token 和时长未暴露，不报告为零，也不据此声称统计稳定性。

## CI

`.github/workflows/test.yml` 在 push 和 pull request 时使用 Python 3.9、3.11、3.12 运行全量测试和风格审计烟测。CI 安装 PyYAML 仅为测试 frontmatter，三个运行时脚本仍只依赖标准库。

## Known limitations

- 正则脚本只能发现已编码的表面差异，不能确定技术方案是否正确。
- 脚本不能判断法规、标准或制度对具体项目的法律适用性。
- 风格命中不构成 AI 作者身份判断，也不应作为作者检测结论。
- 保护项脚本不能发现全部隐含责任、复杂表格关系、图示拓扑和同义术语漂移，仍需人工保真复读。
- 重复保护项检查只能发现词面数量变化，不能判断不同位置的条款、责任或结论是否语义等价。
- 证据检查依赖人工建立 Claim 账本，不能自动穷尽正文中的全部客观主张。
