from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReferenceContractTests(unittest.TestCase):
    def test_formal_template_adaptation_preserves_structure_and_blocks_gaps(self):
        text = (ROOT / "references/formal-template-adaptation.md").read_text(
            encoding="utf-8"
        )
        for phrase in [
            "`source_id`",
            "`source_filename`",
            "`material_status`",
            "`structural_nodes`",
            "`table_relations`",
            "`citation_locations`",
            "`extraction_gaps`",
            "不是新的正式材料",
            "正式模板控制章节、编号、表格和必填项",
            "内容责任",
            "建议提纲",
            "OCR 不确定",
            "表格关系丢失",
            "图示无法恢复",
            "高风险结论",
            "不实现 DOCX、PDF、Excel、OCR 或图像解析器",
            "Python 标准库",
        ]:
            self.assertIn(phrase, text)

    def test_governance_operation_reference_defines_catalog_and_boundaries(self):
        text = (ROOT / "references/governance-operation.md").read_text(
            encoding="utf-8"
        )
        for phrase in [
            "`policy_development`",
            "`publication_execution`",
            "`inspection_evaluation`",
            "`emergency_response`",
            "`revision`",
            "`management_policy`",
            "`management_measures`",
            "`operating_procedure`",
            "`emergency_plan`",
            "`emergency_drill_plan`",
            "`special_response_plan`",
            "`governance_report`",
            "`governance_review_material`",
            "`policy_revision`",
            "`recognition_coverage`",
            "`basic_support`",
            "H3",
            "不推断组织职责或制度效力",
        ]:
            self.assertIn(phrase, text)

    def test_research_project_reference_defines_catalog_and_support_boundary(self):
        text = (ROOT / "references/research-project.md").read_text(
            encoding="utf-8"
        )
        for phrase in [
            "`application`",
            "`task_agreement`",
            "`research_implementation`",
            "`midterm_review`",
            "`final_acceptance`",
            "`research_application`",
            "`research_feasibility_assessment`",
            "`research_task_agreement`",
            "`research_implementation_plan`",
            "`research_interim_report`",
            "`research_interim_inspection`",
            "`research_final_acceptance`",
            "`recognition_coverage`",
            "`basic_support`",
            "不补造科研管理要求",
        ]:
            self.assertIn(phrase, text)

    def test_writing_preparation_contract_separates_two_stage_and_quick_path(self):
        text = (ROOT / "references/writing-preparation.md").read_text(
            encoding="utf-8"
        )
        for phrase in [
            "`two_stage`",
            "`quick_path`",
            "材料清单",
            "材料关系",
            "感知维度",
            "控制性材料",
            "事实与判断",
            "假设",
            "冲突",
            "待确认项",
            "追溯摘要",
            "拟加载合同",
            "已确认",
            "需要用户确认",
            "不输出隐藏推理",
            "保护项",
            "证据状态",
            "陈述效力",
            "H1—H6",
        ]:
            self.assertIn(phrase, text)

    def test_material_contract_registry_defines_evidence_and_privacy_gates(self):
        text = (ROOT / "references/material-contract-evidence.md").read_text(
            encoding="utf-8"
        )
        for phrase in [
            "适用的业务域、生命周期位置、文种场景和材料子类型",
            "`required_inputs`",
            "`content_responsibilities`",
            "`reasonable_depth`",
            "`statement_force`",
            "`traceability`",
            "`common_failures`",
            "`missing_information_handling`",
            "`validation_case_ids`",
            "`support_level`",
            "`authorization`",
            "`redaction_status`",
            "`material_version`",
            "`review_status`",
            "`case_type`",
            "`evidence_type`",
            "`model_execution`",
            "`project_restricted`",
            "`prohibited_persistence`",
            "`deep_support`",
            "`joint_review_support`",
            "不计入正式要求或真实案例数量",
        ]:
            self.assertIn(phrase, text)

    def test_project_context_requires_confirmation_isolation_and_secret_rejection(self):
        text = (ROOT / "references/project-context.md").read_text(
            encoding="utf-8"
        )
        for phrase in [
            "可选本地工件",
            "`actor: user`",
            "`confirmed`",
            "`rejected`",
            "`pending`",
            "`pending_review`",
            "项目隔离",
            "不得自动合并",
            "密钥",
            "口令",
            "令牌",
            "真实账号",
            "无必要个人信息",
            "不自动调用外部网络",
            "外部数据库",
        ]:
            self.assertIn(phrase, text)

    def test_material_set_review_requires_explicit_relations_and_blocks_conflicts(self):
        text = (ROOT / "references/material-set-review.md").read_text(
            encoding="utf-8"
        )
        for phrase in [
            "governs",
            "derives_from",
            "supersedes",
            "implements",
            "verifies",
            "conflicts_with",
            "unclear",
            "文件日期",
            "批准",
            "签署",
            "`approved`",
            "`signed`",
            "用户指定",
            "范围",
            "数量",
            "参数",
            "责任",
            "时间",
            "结论",
            "陈述效力",
            "无法验证跨阶段一致性",
            "跨材料关系",
            "`not_provided`",
            "`provide_conflict_dimension_and_impact`",
            "`relation_id`",
            "不代替",
        ]:
            self.assertIn(phrase, text)

    def test_statement_force_policy_keeps_force_orthogonal_and_conservative(self):
        text = (ROOT / "references/statement-force-policy.md").read_text(
            encoding="utf-8"
        )
        for phrase in [
            "assumption",
            "professional_judgment",
            "recommended_solution",
            "approved_boundary",
            "contractual_commitment",
            "implementation_fact",
            "acceptance_conclusion",
            "SUPPORTED",
            "NEEDS_USER_CONFIRMATION",
            "文种转换",
            "因果外推",
        ]:
            self.assertIn(phrase, text)

    def test_structural_antipatterns_have_required_checks(self):
        text = (ROOT / "references/structural-antipatterns.md").read_text(encoding="utf-8")
        for phrase in ["段落换序", "信息增量", "机械同构", "空转总结", "方案比选"]:
            self.assertIn(phrase, text)

    def test_style_contract_has_four_hard_principles(self):
        text = (ROOT / "references/organization-style-contract.md").read_text(encoding="utf-8")
        for phrase in ["事实不漂移", "术语不替换", "责任不模糊", "正式度不降低"]:
            self.assertIn(phrase, text)

    def test_quality_gate_defines_h1_to_h6(self):
        text = (ROOT / "references/quality-gate.md").read_text(encoding="utf-8")
        for gate in ["H1", "H2", "H3", "H4", "H5", "H6"]:
            self.assertIn(gate, text)


if __name__ == "__main__":
    unittest.main()
