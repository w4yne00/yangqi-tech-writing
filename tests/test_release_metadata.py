from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class ReleaseMetadataTests(unittest.TestCase):
    def test_public_text_is_sanitized(self):
        forbidden = ("央" + "国企", "央" + "企")
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

    def test_version_is_1_0_0(self):
        path = ROOT / "VERSION"
        self.assertTrue(path.is_file(), "VERSION")
        self.assertEqual("1.0.0", path.read_text(encoding="utf-8").strip())

    def test_readme_names_release_and_boundaries(self):
        path = ROOT / "README.md"
        self.assertTrue(path.is_file(), "README.md")
        text = path.read_text(encoding="utf-8")
        for phrase in ["yangqi-tech-writing", "v1.0.0", "七类场景", "H1—H6", "不判断作者身份", "MIT"]:
            self.assertIn(phrase, text)

    def test_release_documents_exist(self):
        for name in ["LICENSE", "CHANGELOG.md", "ROADMAP.md", ".gitignore"]:
            self.assertTrue((ROOT / name).is_file(), name)
        testing = (ROOT / "TESTING.md").read_text(encoding="utf-8")
        self.assertIn("27 项", testing)
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

if __name__ == "__main__":
    unittest.main()
