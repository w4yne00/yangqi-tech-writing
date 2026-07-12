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

    def test_extended_standard_ids_and_metrics(self):
        text = ("依据JR/T 0071—2020和ISO/IEC 27001:2022实施；峰值12000 QPS，"
                "平均时延不高于80ms，可用率99.95%，地址10.20.0.0/16，端口8443，版本V3.2.1。")
        found = extract_protected(text)
        self.assertEqual(["JR/T 0071—2020", "ISO/IEC 27001:2022"], found["standard_id"])
        self.assertIn("12000 QPS", found["throughput_metric"])
        self.assertIn("10.20.0.0/16", found["network_identifier"])
        self.assertIn("V3.2.1", found["software_version"])

    def test_path_and_plain_version_words_are_not_overmatched(self):
        found = extract_protected("文件位于docs/T 0071/example，版本管理由使用单位负责。")
        self.assertEqual([], found["standard_id"])
        self.assertEqual([], found["software_version"])

    def test_date_range_deadline_and_compound_owner(self):
        text = ("建设单位和运维单位应于2026年7月1日至8月31日完成联调，"
                "归口管理部门应在5个工作日内复核，整改不晚于2026年9月底。")
        found = extract_protected(text)
        self.assertIn("2026年7月1日至8月31日", found["date_range"])
        self.assertIn("5个工作日内", found["deadline"])
        for owner in ("建设单位", "运维单位", "归口管理部门"):
            self.assertIn(owner, found["responsible_party"])

    def test_bare_year_and_generic_unit_are_not_complete_entities(self):
        found = extract_protected("2026年持续推进，各单位结合实际研究。")
        self.assertEqual([], found["date"])
        self.assertNotIn("单位", found["responsible_party"])

    def test_normative_phrase_change_is_reported(self):
        report = compare_texts("时延不得高于80ms，上线不晚于8月底。", "时延建议控制在80ms，上线计划在8月底。")
        self.assertIn("不得高于", report["normative_changes"])
        self.assertIn("不晚于", report["normative_changes"])

    def test_duplicate_standard_occurrence_loss_is_blocked(self):
        before = "系统应符合GB/T 25070—2019。复核时仍应符合GB/T 25070—2019。"
        after = "系统应符合GB/T 25070—2019。复核时仍应符合要求。"
        report = compare_texts(before, after)
        self.assertFalse(report["passed"])
        self.assertEqual(["GB/T 25070—2019"], report["missing"]["standard_id"])
        self.assertEqual(1, report["missing_counts"]["standard_id"]["GB/T 25070—2019"])

    def test_duplicate_responsible_party_loss_is_blocked(self):
        report = compare_texts(
            "建设单位负责建设，建设单位负责验收。",
            "建设单位负责建设，项目组负责验收。",
        )
        self.assertFalse(report["passed"])
        self.assertEqual(1, report["missing_counts"]["responsible_party"]["建设单位"])

    def test_duplicate_amount_and_date_losses_are_counted(self):
        before = "预算100万元，调整后仍为100万元；2026年8月15日复核，2026年8月15日确认。"
        after = "预算100万元；2026年8月15日复核。"
        report = compare_texts(before, after)
        self.assertEqual(1, report["missing_counts"]["amount"]["100万元"])
        self.assertEqual(1, report["missing_counts"]["date"]["2026年8月15日"])

    def test_equal_duplicate_counts_pass(self):
        text = "建设单位应符合GB/T 25070—2019；建设单位复核时仍应符合GB/T 25070—2019。"
        report = compare_texts(text, text)
        self.assertTrue(report["passed"])
        self.assertEqual({}, report["missing_counts"])

    def test_added_duplicate_is_not_missing(self):
        before = "系统应符合GB/T 25070—2019。"
        after = "系统应符合GB/T 25070—2019，复核仍应符合GB/T 25070—2019。"
        report = compare_texts(before, after)
        self.assertNotIn("standard_id", report["missing_counts"])


if __name__ == "__main__":
    unittest.main()
