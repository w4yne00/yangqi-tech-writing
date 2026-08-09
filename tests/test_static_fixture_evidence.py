import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class StaticFixtureEvidenceTests(unittest.TestCase):
    def test_static_fixture_metadata_is_not_model_evidence(self):
        data = json.loads((ROOT / "evals/static-fixture-results.json").read_text(encoding="utf-8"))
        self.assertEqual("v1.1.0", data["version"])
        self.assertEqual("deterministic-static-fixture", data["evidence_type"])
        self.assertFalse(data["model_execution"])
        self.assertFalse(data["real_engineering_evidence"])
        self.assertEqual(8, data["case_count"])
        self.assertEqual(16, data["assertions"]["total"])
        self.assertEqual(16, data["assertions"]["passed"])
        self.assertIn("不代表模型运行通过率", data["statement"])

    def test_public_docs_use_static_fixture_wording(self):
        for name in ("TESTING.md", "CHANGELOG.md", "ROADMAP.md"):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("确定性规则夹具", text, name)
            self.assertIn("不代表模型运行通过率", text, name)

    def test_dynamic_forward_gate_is_not_embedded_in_static_fixture(self):
        data = json.loads((ROOT / "evals/static-fixture-results.json").read_text(encoding="utf-8"))
        self.assertNotIn("pending_release_gate", data)

        testing = (ROOT / "TESTING.md").read_text(encoding="utf-8")
        handoff = (ROOT / "docs/codex-handoff.md").read_text(encoding="utf-8")
        self.assertIn("真实前向复测", testing)
        self.assertIn("9/9", testing)
        self.assertIn("真实前向复测", handoff)
        self.assertIn("released as stable v1.1.0", handoff)


if __name__ == "__main__":
    unittest.main()
