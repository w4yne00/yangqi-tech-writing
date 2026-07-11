from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReferenceContractTests(unittest.TestCase):
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
