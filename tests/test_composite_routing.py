from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CompositeRoutingTests(unittest.TestCase):
    def test_policy_has_precedence_and_four_examples(self):
        text = (ROOT / "references/composite-routing.md").read_text(encoding="utf-8")
        for phrase in ("主文种", "局部文种", "风险更高", "可研＋架构",
                       "投标＋招标原文", "汇报＋验收结论", "制度＋会议纪要"):
            self.assertIn(phrase, text)

    def test_skill_links_policy_and_annotation_boundaries(self):
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("references/composite-routing.md", text)
        self.assertIn("只输出诊断", text)
        self.assertIn("不输出改写稿", text)
        self.assertIn("不输出完整改写稿", text)
        self.assertIn("没有实质问题时明确说明无需调整", text)

    def test_readme_uses_same_annotation_contract(self):
        text = (ROOT / "README.md").read_text(encoding="utf-8")
        section = text.split("### Annotation mode", 1)[1].split("\n## ", 1)[0]
        for field in ("定位", "问题类型", "影响", "风险级别", "建议动作", "是否建议改写"):
            self.assertIn(field, section)
        self.assertIn("无需调整", section)


if __name__ == "__main__": unittest.main()
