from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCENES = {
    "feasibility-study.md": "bounded",
    "architecture-design.md": "in-place",
    "technical-spec.md": "in-place",
    "bid-response.md": "in-place",
    "security-policy.md": "in-place",
    "presentation.md": "structural",
    "review-acceptance.md": "in-place",
}
REQUIRED_HEADINGS = (
    "识别信号", "写作目标", "默认策略", "强保护项",
    "应处理", "禁止动作", "输出要求",
)


class ScenePackTests(unittest.TestCase):
    def test_each_scene_has_contract_and_scope(self):
        base = ROOT / "references/scene-packs"
        for filename, scope in SCENES.items():
            text = (base / filename).read_text(encoding="utf-8")
            with self.subTest(filename=filename):
                for heading in REQUIRED_HEADINGS:
                    self.assertIn(heading, text)
                self.assertIn(scope, text)


if __name__ == "__main__":
    unittest.main()
