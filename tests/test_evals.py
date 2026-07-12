import json
from pathlib import Path
import unittest
from collections import Counter


ROOT = Path(__file__).resolve().parents[1]


class EvalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "evals/evals.json").read_text(encoding="utf-8"))

    def test_count_ids_and_skill_name(self):
        evals = self.data["evals"]
        self.assertEqual("yangqi-tech-writing", self.data["skill_name"])
        self.assertEqual("v1.1.0", self.data["version"])
        self.assertEqual(43, len(evals))
        self.assertEqual(list(range(1, 44)), [item["id"] for item in evals])
        self.assertEqual(43, len({item["case_id"] for item in evals}))

    def test_rc2_cases_are_unchanged(self):
        old = json.loads((ROOT / "tests/fixtures/v1.1.0-rc.2-evals.json").read_text(encoding="utf-8"))
        self.assertEqual(old["evals"], self.data["evals"][:40])

    def test_annotation_cases_use_one_compatible_contract(self):
        cases = {item["case_id"]: item for item in self.data["evals"]}
        fields = ("定位", "问题类型", "影响", "风险级别", "建议动作", "是否建议改写")
        for case_id in ("X-ANN-24", "H-ANN-37"):
            text = " ".join(cases[case_id]["expectations"])
            for field in fields:
                self.assertIn(field, text, (case_id, field))
        no_issue = " ".join(cases["H-ANN-38"]["expectations"])
        self.assertIn("无需调整", no_issue)
        self.assertIn("不制造", no_issue)

    def test_v110_categories_remain_balanced(self):
        counts = Counter(item["category"] for item in self.data["evals"][24:40])
        self.assertEqual({"protected_near_miss":4,"audit_near_miss":4,
                          "composite_scene":4,"annotation":2,"evidence_gate":2}, dict(counts))

    def test_rc3_causal_boundary_cases(self):
        new = self.data["evals"][40:]
        self.assertEqual(["C-CAU-41", "C-CAU-42", "C-CAU-43"], [item["case_id"] for item in new])
        self.assertTrue(all(item["category"] == "causal_boundary" for item in new))
        for item in new:
            self.assertGreaterEqual(len(item["expectations"]), 2)

    def test_all_seven_scenes_are_covered(self):
        scenes = {item["scene"] for item in self.data["evals"]}
        required = {
            "feasibility-study", "architecture-design", "technical-spec",
            "bid-response", "security-policy", "presentation", "review-acceptance",
        }
        self.assertTrue(required.issubset(scenes))

    def test_each_eval_has_verifiable_expectations(self):
        for item in self.data["evals"]:
            with self.subTest(case_id=item["case_id"]):
                self.assertGreaterEqual(len(item["expectations"]), 2)
                self.assertTrue(all(isinstance(value, str) and value.strip() for value in item["expectations"]))


if __name__ == "__main__":
    unittest.main()
