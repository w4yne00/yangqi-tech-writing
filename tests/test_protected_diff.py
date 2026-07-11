import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from protected_diff import compare_texts, extract_protected


class ProtectedDiffTests(unittest.TestCase):
    def test_extracts_policy_standard_amount_date_and_metrics(self):
        text = (
            "根据发改投资规〔2023〕304号和GB/T 25070—2019，"
            "项目投资6800万元，计划于2027年12月完成，"
            "核心业务RTO为30分钟，RPO为5分钟。"
        )
        found = extract_protected(text)
        flattened = {item for values in found.values() for item in values}
        for expected in [
            "发改投资规〔2023〕304号",
            "GB/T 25070—2019",
            "6800万元",
            "2027年12月",
            "RTO为30分钟",
            "RPO为5分钟",
        ]:
            self.assertIn(expected, flattened)

    def test_reports_missing_protected_item(self):
        before = "承建方应在2026年8月15日前完成整改。"
        after = "项目组应完成整改。"
        report = compare_texts(before, after)
        missing = {item for values in report["missing"].values() for item in values}
        self.assertIn("承建方", missing)
        self.assertIn("2026年8月15日", missing)

    def test_reports_normative_strength_change(self):
        report = compare_texts("平台应记录操作。", "平台可记录操作。")
        self.assertFalse(report["passed"])
        self.assertEqual(1, report["normative_changes"]["应"]["before"])
        self.assertEqual(0, report["normative_changes"]["应"]["after"])


if __name__ == "__main__":
    unittest.main()
