import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from style_audit import audit_text


class StyleAuditTests(unittest.TestCase):
    def test_flags_clear_t1_patterns(self):
        report = audit_text("本项目将全面赋能集团发展，打造行业标杆。综上所述，前景广阔。")
        hits = {hit["pattern"] for hit in report["hits"]}
        self.assertTrue({"全面赋能", "行业标杆", "综上所述", "前景广阔"}.issubset(hits))

    def test_does_not_flag_quoted_teaching_example(self):
        report = audit_text("制度编写应避免“全面赋能安全治理”这类空泛表述。")
        self.assertEqual([], report["hits"])

    def test_reports_sentence_length_variation(self):
        report = audit_text("短句。这里是一句长度明显更长、用于说明测试目标和处理边界的句子。")
        self.assertGreater(report["metrics"]["sentence_length_cv"], 0)

    def test_markdown_quote_and_teaching_line_are_exempt(self):
        report = audit_text("> 原文：本项目具有重要里程碑意义。\n\n禁用词示例：全面赋能、行业标杆。")
        self.assertEqual(0, report["summary"]["t1"])
        self.assertGreaterEqual(report["summary"]["exempted_count"], 2)

    def test_same_phrase_in_body_is_detected(self):
        report = audit_text("本项目将全面赋能各单位，打造行业标杆。")
        self.assertTrue({"全面赋能", "行业标杆"}.issubset({h["pattern"] for h in report["hits"]}))

    def test_technical_closed_loop_field_is_not_slogan(self):
        report = audit_text("字段event_closed表示事件闭环状态。")
        self.assertFalse(any(hit["pattern"] == "闭环" for hit in report["hits"]))

    def test_repeated_same_transition_triggers_t2(self):
        report = audit_text("此外，应核对范围。此外，应核对责任。此外，应核对时限。")
        hits = [h for h in report["hits"] if h["tier"] == "T2" and h["pattern"] == "transition"]
        self.assertEqual(1, len(hits))
        self.assertEqual(3, hits[0]["occurrences"])

    def test_output_is_deterministic_and_additive(self):
        text = "此外，应核对范围。同时，应核对责任。"
        first, second = audit_text(text), audit_text(text)
        self.assertEqual(first, second)
        self.assertTrue({"hits","metrics","summary"}.issubset(first))
        self.assertEqual("not_applicable", first["summary"]["authorship_verdict"])


if __name__ == "__main__":
    unittest.main()
