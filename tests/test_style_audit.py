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


if __name__ == "__main__":
    unittest.main()
