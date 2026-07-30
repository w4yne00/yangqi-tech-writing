from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReferenceContractTests(unittest.TestCase):
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
