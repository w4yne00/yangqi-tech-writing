import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class TriggerEvalTests(unittest.TestCase):
    def test_count_balance_and_unique_queries(self):
        data = json.loads((ROOT / "evals/trigger-evals.json").read_text(encoding="utf-8"))
        self.assertEqual(20, len(data))
        self.assertEqual(20, len({item["query"] for item in data}))
        self.assertEqual(10, sum(item["should_trigger"] for item in data))

    def test_fields_and_negative_near_misses(self):
        data = json.loads((ROOT / "evals/trigger-evals.json").read_text(encoding="utf-8"))
        for item in data:
            self.assertEqual({"query","should_trigger","category","rationale"}, set(item))
        negative = {x["category"] for x in data if not x["should_trigger"]}
        self.assertTrue({"formatting","technical_correctness","personal_imitation",
                         "general_content","code"}.issubset(negative))

    def test_recorded_trigger_accuracy(self):
        data = json.loads((ROOT / "evals/trigger-results.json").read_text(encoding="utf-8"))
        candidate = data["candidate"]
        self.assertEqual(20, len(candidate))
        accuracy = sum(x["expected"] == x["predicted"] for x in candidate) / len(candidate)
        self.assertGreaterEqual(accuracy, 0.90)
        self.assertTrue(all(x["predicted"] for x in candidate if x.get("high_risk")))


if __name__ == "__main__": unittest.main()
