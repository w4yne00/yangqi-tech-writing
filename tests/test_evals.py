import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class EvalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT / "evals/evals.json").read_text(encoding="utf-8"))

    def test_count_ids_and_skill_name(self):
        evals = self.data["evals"]
        self.assertEqual("yangqi-tech-writing", self.data["skill_name"])
        self.assertEqual(24, len(evals))
        self.assertEqual(list(range(1, 25)), [item["id"] for item in evals])
        self.assertEqual(24, len({item["case_id"] for item in evals}))

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
