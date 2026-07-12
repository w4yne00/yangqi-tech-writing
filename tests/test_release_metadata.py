import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReleaseMetadataTests(unittest.TestCase):
    def test_public_text_is_sanitized(self):
        forbidden = ("\u592e\u56fd\u4f01", "\u592e\u4f01")
        suffixes = {".md", ".json", ".py", ".yml", ".yaml"}
        leaks = {}
        for path in ROOT.rglob("*"):
            if not path.is_file() or ".git" in path.parts or "__pycache__" in path.parts:
                continue
            if path.suffix.lower() not in suffixes:
                continue
            text = path.read_text(encoding="utf-8")
            hits = [term for term in forbidden if term in text]
            if hits:
                leaks[str(path.relative_to(ROOT))] = hits
        self.assertEqual({}, leaks)
        for name in ["SKILL.md", "README.md", "evals/evals.json"]:
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("G 企", text, name)

    def test_version_is_stable_release(self):
        path = ROOT / "VERSION"
        self.assertTrue(path.is_file(), "VERSION")
        self.assertEqual("1.1.0", path.read_text(encoding="utf-8").strip())
        for name in ("README.md", "CHANGELOG.md", "ROADMAP.md", "TESTING.md"):
            self.assertIn("1.1.0", (ROOT / name).read_text(encoding="utf-8"))

    def test_readme_reports_v1_1_0_as_stable(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("当前稳定版本：`v1.1.0`", readme)
        self.assertNotIn("本地候选版本", readme)

    def test_readme_names_release_and_boundaries(self):
        path = ROOT / "README.md"
        self.assertTrue(path.is_file(), "README.md")
        text = path.read_text(encoding="utf-8")
        for phrase in ["yangqi-tech-writing", "v1.1.0", "七类场景", "H1—H6", "不判断作者身份", "MIT"]:
            self.assertIn(phrase, text)

    def test_release_documents_exist(self):
        for name in ["LICENSE", "CHANGELOG.md", "ROADMAP.md", ".gitignore"]:
            self.assertTrue((ROOT / name).is_file(), name)
        testing = (ROOT / "TESTING.md").read_text(encoding="utf-8")
        self.assertIn("45 项", testing)
        self.assertNotIn("skill-https-github-com-oubigfa-de", testing)

    def test_ci_matrix_and_commands(self):
        path = ROOT / ".github/workflows/test.yml"
        self.assertTrue(path.is_file(), ".github/workflows/test.yml")
        text = path.read_text(encoding="utf-8")
        for token in [
            "3.9", "3.11", "3.12", "unittest discover -s tests -v",
            "style_audit.py tests/fixtures/sample.md",
        ]:
            self.assertIn(token, text)

    def test_readme_reports_43_behavior_evals(self):
        data = json.loads((ROOT / "evals/evals.json").read_text(encoding="utf-8"))
        self.assertEqual(43, len(data["evals"]))
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("43 项行为评测", readme)
        self.assertNotIn("evals/evals.json         # 24 项行为评测", readme)

    def test_handoff_records_v110_release(self):
        text = (ROOT / "docs/codex-handoff.md").read_text(encoding="utf-8")
        for phrase in ("Stable: `v1.1.0`", "FWD-01", "因果外推", "真实前向复测", "66", "released as stable v1.1.0"):
            self.assertIn(phrase, text)

if __name__ == "__main__":
    unittest.main()
