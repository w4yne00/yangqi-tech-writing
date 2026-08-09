from pathlib import Path
import re
import unittest

import yaml


ROOT = Path(__file__).resolve().parents[1]

ANNOTATION_FIELDS = (
    "定位", "问题类型", "影响", "风险级别", "建议动作", "是否建议改写",
)

REQUIRED_FILES = [
    "SKILL.md",
    "README.md",
    "TESTING.md",
    "references/protected-spans.md",
    "references/evidence-policy.md",
    "references/statement-force-policy.md",
    "references/material-set-review.md",
    "references/writing-preparation.md",
    "references/project-context.md",
    "references/material-contract-evidence.md",
    "references/governance-operation.md",
    "references/research-project.md",
    "references/ai-trace-patterns.md",
    "references/structural-antipatterns.md",
    "references/organization-style-contract.md",
    "references/quality-gate.md",
    "references/scene-packs/feasibility-study.md",
    "references/scene-packs/architecture-design.md",
    "references/scene-packs/technical-spec.md",
    "references/scene-packs/bid-response.md",
    "references/scene-packs/security-policy.md",
    "references/scene-packs/presentation.md",
    "references/scene-packs/review-acceptance.md",
    "scripts/protected_diff.py",
    "scripts/evidence_check.py",
    "scripts/style_audit.py",
    "scripts/material_contract_registry.py",
    "templates/material-contract-evidence-bundle.json",
    "evals/evals.json",
]


class StructureTests(unittest.TestCase):
    def test_required_files_exist(self):
        missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
        self.assertEqual([], missing)

    def test_skill_name_matches_directory(self):
        skill_file = ROOT / "SKILL.md"
        self.assertTrue(skill_file.is_file(), "SKILL.md not found")
        content = skill_file.read_text(encoding="utf-8")
        self.assertIn("name: yangqi-tech-writing", content)

    def test_frontmatter_and_trigger_description(self):
        content = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        self.assertIsNotNone(match)
        metadata = yaml.safe_load(match.group(1))
        self.assertEqual("yangqi-tech-writing", metadata["name"])
        description = metadata["description"]
        for phrase in [
            "可研", "初设", "总体架构", "技术规范", "招标需求", "投标应答",
            "安全制度", "应急预案", "汇报PPT", "评审意见", "验收报告", "会议纪要",
            "起草", "审阅", "改写", "去AI", "证据",
        ]:
            self.assertIn(phrase, description)
        for phrase in ["不用于", "技术正确性", "排版"]:
            self.assertIn(phrase, description)

    def test_frontmatter_uses_portable_fields_only(self):
        content = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", content, re.DOTALL)
        self.assertIsNotNone(match)
        metadata = yaml.safe_load(match.group(1))
        self.assertEqual({"name", "description"}, set(metadata))
        self.assertNotIn("compatibility", metadata)

    def test_skill_is_progressive_and_execution_order_is_fixed(self):
        content = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertLess(len(content.splitlines()), 500)
        section = content.split("## 固定执行顺序", 1)[1].split("\n## ", 1)[0]
        order = [
            "场景", "保护项", "证据", "陈述效力", "材料关系",
            "项目上下文", "Tier", "档位", "scope", "改写", "两遍复读",
            "质量闸门",
        ]
        positions = [section.find(token) for token in order]
        self.assertTrue(all(position >= 0 for position in positions), positions)
        self.assertEqual(sorted(positions), positions)

    def test_annotation_and_default_output_contract_exist(self):
        content = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("Annotation mode", content)
        self.assertIn("默认输出合同", content)
        self.assertIn("不输出改写稿", content)
        annotation = content.split("### Annotation mode", 1)[1].split("\n## ", 1)[0]
        for field in ANNOTATION_FIELDS:
            self.assertIn(field, annotation)
        for value in ("高", "中", "低", "是", "否", "待确认"):
            self.assertIn(value, annotation)

    def test_linked_local_references_exist(self):
        content = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        links = re.findall(r"\[[^\]]+\]\(([^)]+\.md)\)", content)
        self.assertGreaterEqual(len(links), 7)
        missing = [link for link in links if not (ROOT / link).is_file()]
        self.assertEqual([], missing)


if __name__ == "__main__":
    unittest.main()
