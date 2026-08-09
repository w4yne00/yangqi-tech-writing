# Testing

验证日期：2026-08-09；稳定版本：`1.1.0`。

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
python3 -m unittest tests.test_project_context -v
python3 -m unittest tests.test_material_contract_registry -v
python3 -m unittest tests.test_foundation_synthetic_benchmark -v
python3 scripts/material_contract_registry.py templates/material-contract-evidence-bundle.json
python3 -m json.tool evals/evals.json
python3 -m json.tool evals/trigger-evals.json
python3 -m json.tool evals/trigger-results.json
python3 -m json.tool evals/static-fixture-results.json
python3 -m json.tool evals/foundation-synthetic-benchmark.json
```

安装了本地 `skill-creator` 时，还可执行：

```bash
python3 "$HOME/.agents/skills/skill-creator/scripts/quick_validate.py" .
```

## Results

- Foundation 12 当前根目录完整单元测试为 202 项通过、0 项失败；统一基准、产品 JSON、Skill 结构、Markdown 链接、版本和隐私检查均通过。
- Foundation 12 新增 26 个统一基准案例和 7 项集成测试，覆盖三个业务域、七类场景、生命周期近失配、复合材料、陈述效力强化/弱化边界、快速/两阶段模式、七类材料关系、七类冲突阻断、上下文确认更新与项目隔离、正式模板、提取缺口和禁止持久化边界。
- 统一基准复核既有 43 项行为评测、20 项触发边界、三个审计脚本 `2/2/0` 退出码和稳定版 `1.1.0` 元数据。全部案例均为确定性合成输入，`model_execution: false`，属于非真实工程证据；结果只支持识别覆盖和基础支持，不构成深度支持、联审支持、前向验证或统计稳定性证明。

- Foundation 10 当前根目录完整单元测试为 194 项通过、0 项失败；最高层感知入口、正式模板适配合同、公开链接、版本和隐私检查均通过。
- Foundation 10 新增 7 项最高层外部行为测试和 1 项参考合同测试：标准化视图保留文件名、标题条款层级、页表图定位、表格关系、引用位置和提取缺口；正式模板存在时控制章节、编号、表格和必填项，材料合同只检查内容责任；无模板时才返回明确标记为建议、非正式且可调整的推荐提纲。
- OCR 不确定、表格关系丢失和图示无法恢复三类缺口在显式关联高风险 Claim 时阻断并取消允许陈述效力；低风险依赖只记录缺口。核心未实现 DOCX、PDF、Excel、OCR 或图像解析器，运行时继续只使用 Python 标准库且未新增第三方依赖。
- Foundation 10 完整验证中，三个 CLI 烟测退出码为 `2`、`2`、`0`；四个产品 JSON 和两个既有前向 JSON 解析通过，根目录 Skill 校验返回 `Skill is valid!`。旧 `outputs/yangqi-tech-writing-v1.1.0-rc.3` 副本独立通过 66 项测试、Skill 校验和四个产品 JSON 解析；该只读回归不表示 Foundation 10 已写入旧发布候选。
- 代码审查后补充证据冲突与提取缺口并存、整份新建与材料集阻断不被 `two_stage` 覆盖两项组合回归；证据处理动作与 `extraction_gap_action` 分开记录，定位可用性检查复用同一规则。
- Foundation 05 当前根目录完整单元测试为 186 项通过、0 项失败；七类场景正向识别、复合材料联合路由、公开合同链接和既有稳定行为均通过。
- Foundation 05 新增 7 个七类场景正向案例、2 个确定性合成复合材料案例、8 项最高层接缝外部行为测试和 1 项复合路由参考合同测试。初步设计评审汇报保留 `engineering_construction`、`design`、`presentation` 主场景和 `review_acceptance` 局部场景；科研课题结题验收汇报保留 `research_project`、`final_acceptance` 及同一复合关系。
- 复合路由分别输出主、局部场景的适用内容和保护边界，局部内容采用更严格的 `in_place`；缺少专用材料合同时在新建、续写和局部任务中均加载两个既有场景基础合同，支持级别保持 `recognition_coverage` 或 `basic_support`。初设正文、科研结题验收材料、工程结题验收汇报及仅引用复合材料名称的近失配仍保持原身份。合成夹具标记为 `deterministic-synthetic-fixture`、`model_execution: false`，不构成深度支持、联审支持、前向验证或真实复合材料表现证据。
- Foundation 04 当前根目录完整单元测试为 177 项通过、0 项失败；治理运行域识别覆盖、最高层感知入口、公开合同链接和既有稳定行为均通过。
- Foundation 04 新增 9 个确定性合成治理材料案例、8 项最高层接缝外部行为测试和 1 项治理参考合同测试，覆盖制度制定、发布执行、检查评估、应急处置和修订位置，以及管理制度、管理办法、操作规程、应急预案、演练方案、专项处置方案、治理汇报、治理评审和制度修订材料。
- 治理汇报同时输出 `governance_operation`、`inspection_evaluation` 与 `presentation`；制度正文、操作规程和应急预案保持不同材料子类型。明确局部制度任务加载既有安全制度场景、保护项、陈述效力与 H1—H6，整份新建只声明 `recognition_coverage` 并进入写作准备单。上位名称只返回带依据候选并进入 `conservative_audit`，正文仅引用治理材料不会改变主材料身份；不补造组织职责或制度效力。合成夹具继续标记为 `deterministic-synthetic-fixture`、`model_execution: false`，不构成深度支持、联审支持、前向验证或真实治理材料表现证据。
- Foundation 03 当前根目录完整单元测试为 168 项通过、0 项失败；科研课题域识别覆盖、最高层感知入口、公开合同链接和既有稳定行为均通过。
- Foundation 03 新增 7 个确定性合成科研材料案例、10 项最高层接缝外部行为测试和 1 项科研参考合同测试，覆盖科研申报书、可研论证、任务书、研究实施方案、中期汇报、中期检查和结题验收材料，以及规格原词、无“报告”后缀和“明确科研归属＋泛称标题”的组合识别。
- 科研实施方案与工程实施方案保持不同业务域和生命周期；科研中期汇报同时输出 `midterm_review` 与 `presentation`；结题验收输出科研域、`final_acceptance` 和科研材料子类型。上位阶段名称及业务域冲突只返回带依据候选并进入 `conservative_audit`；正文通过“依据、引用、参照、参考、根据、按照、基于、见”引用科研材料时不会改变主材料身份。明确局部任务只声明 `basic_support`，整份新建只声明 `recognition_coverage` 并进入写作准备单，不补造科研管理要求。合成夹具继续标记为 `deterministic-synthetic-fixture`、`model_execution: false`，不构成深度支持、联审支持、前向验证或真实科研材料表现证据。
- Foundation 02 当前根目录完整单元测试为 157 项通过、0 项失败；工程建设域识别覆盖、最高层感知入口、公开合同链接和既有稳定行为均通过。
- Foundation 02 新增 14 个确定性合成工程材料案例和 15 项外部行为测试，覆盖立项、设计、采购、实施、试运行、验收、运营七个生命周期位置，以及可研/初设/详设/总体架构、技术规范/投标应答、验收大纲/验收报告等近失配边界。
- 明确的局部工程材料任务只声明 `basic_support` 并加载既有场景基础合同；整份新建只声明 `recognition_coverage` 并进入写作准备单。七类生命周期的上位阶段名称只返回带依据候选、待确认项和共性合同；标题中的主材料身份不会被正文材料或科研课题成果引用覆盖，任务明确否定或替代仍可修正标题，但标题优先级不绕过任务或正文明确给出的业务域约束；“项目”不足以直接认定工程域，肯定的科研/课题归属语境和被否定子类型不会进入工程候选，明确否定科研后给出的工程文种仍可识别。夹具继续标记为 `deterministic-synthetic-fixture`、`model_execution: false`，不构成深度支持、联审支持、前向验证或真实工程表现证据。
- Foundation 07 当前根目录完整单元测试为 142 项通过、0 项失败；最高层感知入口、Skill 结构和新增写作准备单合同均通过。
- Foundation 07 新增 7 项外部行为测试：明确的初步设计完整新建和多材料整合进入 `two_stage`，准备单覆盖材料、关系、感知维度、控制依据、事实与判断、假设、冲突、结构化确认边界、追溯摘要和拟加载合同；边界明确的局部改写、审阅和只标问题进入 `quick_path`。
- 文种不明的普通文档新建不会仅因 `scope: document` 被升级为两阶段；同一进程先处理两阶段任务也不会污染后续任务的合同列表。准备单中的每个未确认 Claim 都会进入公开待确认清单。
- 局部任务存在无来源高效力陈述、待确认项或阻断项时降级为 `conservative_audit`。快速通道继续加载保护项、证据、陈述效力和 H1—H6，不改变任务模式或 Annotation mode 输出边界。测试复用带 `deterministic-synthetic-fixture`、`model_execution: false` 声明的合成输入，不构成真实模型表现证据。
- Foundation 11 当前根目录完整单元测试为 134 项通过、0 项失败；材料合同模板、登记夹具、产品 JSON、Skill 结构、Markdown 链接、版本和公开文本脱敏检查均通过。
- Foundation 11 新增 19 项材料合同与样本登记外部行为测试，覆盖有效基础登记、模板完整性、合同或样本元数据缺失、结构化陈述效力跃迁、授权状态与用途范围、评审状态、未脱敏样本、项目受限用途、禁止持久化信息、正式要求身份、合成证据标记、前向模型执行状态以及错误深度/联审声明。
- 分发模板和测试夹具固定为 `basic_support`，其中的占位合成样本标记为 `deterministic-synthetic-fixture`、`model_execution: false`，不会被计入正式要求或真实案例，也不表示任何具体材料已经获得深度支持、联审支持或前向验证。
- Foundation 09 当前根目录完整单元测试为 114 项通过、0 项失败；三个既有审计脚本烟测分别保持预期退出码 `2`、`2`、`0`，六个产品与合成夹具 JSON、两个 rc.3 前向 JSON、Skill 结构、Markdown 链接、版本和跟踪文件脱敏检查均通过。
- Foundation 09 新增 14 项项目上下文外部行为测试，覆盖可选不落盘、确认更新、拒绝更新、待确认不更新、上游变化传播、项目隔离、本地工件声明、已确认记录完整性、版本检查、秘密和无必要个人信息扫描、敏感键名脱敏、凭据近失配以及本地处理边界。
- 只有 `actor: user` 且状态为 `confirmed` 的请求可以写入已确认事实或关系；`rejected` 和 `pending` 均不修改工件。上游材料变化使关联事实、关系、决策、结论和追溯链进入 `pending_review`。
- 项目上下文包固定为单一 `project_id` 的本地 JSON 工件，不自动调用外部网络、上传服务或外部数据库。合成夹具继续标记为 `deterministic-synthetic-fixture`，不包含真实项目事实，也不构成模型运行证据。
- Foundation 08 当前根目录完整单元测试为 99 项通过、0 项失败；三个既有审计脚本烟测、四个产品 JSON 解析和 Skill 结构校验继续符合原合同。
- Foundation 08 在既有最高层感知决策接缝增加可选 `material_set`：4 组确定性合成材料集案例和 10 项外部行为测试覆盖七类关系、日期近失配、批准/签署/用户指定控制依据、七类冲突、逐项冲突关联、关系覆盖、上游缺失、单材料降级及非法状态/关系/冲突维度。
- 文件日期较新不会自动形成 `supersedes`；材料集只有在显式关系下确定控制和替代线索。范围、数量、参数、责任、时间、结论和陈述效力冲突只输出差异、影响和待确认项，并阻断自动定稿。
- 单材料、上游不完整或只有一份材料的材料集均不会声称完成跨阶段一致性验证。合成夹具继续标记为 `deterministic-synthetic-fixture`，不构成真实材料联审或模型稳定性证据。
- Foundation 06 当前根目录完整单元测试为 88 项通过、0 项失败；三个既有审计脚本烟测保持预期退出码，四个产品 JSON 均可解析，Skill 结构校验通过。
- Foundation 06 在既有最高层感知决策接缝增加 7 类陈述效力和逐项联合决策；正向、强化近失配、弱化近失配、效力不明、高效力无来源及冲突案例均通过。合成夹具继续标记为 `deterministic-synthetic-fixture`，不构成真实模型表现证据。
- 有来源的建议保持 `recommended_solution`，不会因文种转换成为 `approved_boundary`；实施事实也不会被弱化为建议。效力不明时输出待确认项并暂按 `assumption`，冲突和高效力无来源陈述继续阻断定稿。
- 现有因果外推测试全部通过；上游偏差仍不能转写为下游既成事实，陈述效力策略未覆盖同一对象、计划基线和材料时点要求。
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
