from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CausalBoundaryTests(unittest.TestCase):
    def test_evidence_policy_requires_same_object_baseline_and_as_of_time(self):
        text = (ROOT / "references/evidence-policy.md").read_text(encoding="utf-8")
        for phrase in ("同一对象", "计划基线", "材料时点", "可能影响", "已延期"):
            self.assertIn(phrase, text)

    def test_presentation_scene_keeps_downstream_effect_as_risk(self):
        text = (ROOT / "references/scene-packs/presentation.md").read_text(encoding="utf-8")
        for phrase in ("上游事项延期", "下游事项已延期", "可能影响", "风险提示"):
            self.assertIn(phrase, text)

    def test_composite_presentation_acceptance_route_blocks_status_transfer(self):
        text = (ROOT / "references/composite-routing.md").read_text(encoding="utf-8")
        for phrase in (
            "跨对象",
            "计划状态",
            "上游延期",
            "下游已延期",
            "同时具备明确计划基线与可比较材料时点",
            "输入直接确认或正式延期结论",
        ):
            self.assertIn(phrase, text)
        self.assertNotIn("计划基线、材料时点或正式延期结论", text)

    def test_h6_checks_causal_modality(self):
        text = (ROOT / "references/quality-gate.md").read_text(encoding="utf-8")
        for phrase in ("H6", "因果", "既成事实", "风险判断"):
            self.assertIn(phrase, text)


if __name__ == "__main__":
    unittest.main()
