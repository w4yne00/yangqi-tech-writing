# 感知与处理决策合同

本合同是用户任务和材料标准化视图进入七类场景执行链之前的最高层接缝。它只形成可观察的路由决策，不替换场景包、保护项、证据策略或 H1—H6，也不判断技术正确性。

## 输入合同

请求包含 `task` 和 `material_view`：

- `task`：包含用户指令、任务模式和处理范围；任务模式使用 `create`、`continue`、`rewrite`、`review` 或 `annotation`。
- `material_view`：`schema_version` 为 `1.0`，`view_type` 为 `material_normalized_view`，并保留 `source_id`、`material_status`、标题及至少一个带 `locator` 的内容片段。
- `is_formal_material` 必须为 `false`。标准化视图是从来源材料提取的派生输入，不产生新的批准、签署、合同或验收效力。

当前最小定位可以是章节和页码，也可以是其他能够回到来源材料复核的非空定位对象。核心不解析 DOCX、PDF、表格、图片或 OCR。

## 输出合同

输出包含标准化视图的来源摘要和统一决策：

- 业务域、生命周期位置、文种场景和材料子类型均使用 `value`、`confidence`、`candidates` 三字段结构。
- 明确信号使用 `explicit`；信息不足时使用 `unknown` 值和 `unclear` 置信状态，并在候选项中记录依据。
- 任务模式保持用户授权，不因材料分类改变。
- 支持级别只声明 `recognition_coverage` 或 `basic_support`。最小切片不声明深度支持、联审支持或前向验证。
- 处理模式可以是 `quick_path` 或 `conservative_audit`。快速通道仍执行保护项、证据和 H1—H6。
- 加载合同使用稳定的语义标识，不暴露内部目录扫描顺序。
- 待确认项列出阻止确定分类的维度；阻断项只记录不能继续自动处理的事项。

当前明确的初步设计审阅加载以下合同：

1. `common.protected_spans`
2. `common.evidence_policy`
3. `scene.architecture_design`
4. `common.quality_gate_h1_h6`

当前切片只对明确的初步设计 `review` 或 `annotation` 声明基础支持。其他任务模式即使材料分类明确，也只声明识别覆盖并进入保守审阅，等待后续合同扩展。

缺少足够信号、信号被明确否定或相互冲突时，只加载共性保护、证据和质量合同，进入保守审阅；不得为了获得确定分类而补造业务域、生命周期或材料子类型。

## 调用

```bash
python3 scripts/perception_decision.py request.json
python3 scripts/perception_decision.py - < request.json
```

脚本仅依赖 Python 3.9 及以上标准库。请求不满足合同或把标准化视图标记为正式材料时，返回退出码 `1`，并在标准错误输出结构化的 `invalid_request`。
