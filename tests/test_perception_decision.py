from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/perception_decision.py"
FIXTURE = ROOT / "tests/fixtures/perception-decision-cases.json"


class PerceptionDecisionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def run_raw(self, request):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "-"],
            input=json.dumps(request, ensure_ascii=False),
            capture_output=True,
            check=False,
            text=True,
        )

    def run_decision(self, request):
        completed = self.run_raw(request)
        self.assertEqual(0, completed.returncode, completed.stderr)
        return json.loads(completed.stdout)

    def test_explicit_preliminary_design_review_returns_observable_decision(self):
        result = self.run_decision(self.fixture["cases"][0]["request"])

        self.assertEqual(
            {
                "source_id": "SYNTHETIC-SOURCE-001",
                "material_status": "draft",
                "locator": {"section": "5.2", "page": 17},
                "is_formal_material": False,
                "view_role": "derived_normalized_view",
            },
            result["material_view"],
        )

        decision = result["decision"]
        self.assertEqual(
            "engineering_construction", decision["business_domain"]["value"]
        )
        self.assertEqual("design", decision["lifecycle_position"]["value"])
        self.assertEqual("architecture_design", decision["document_scene"]["value"])
        self.assertEqual(
            "preliminary_design", decision["material_subtype"]["value"]
        )
        self.assertEqual("review", decision["task_mode"])
        self.assertEqual("basic_support", decision["support_level"])
        self.assertEqual("quick_path", decision["processing_mode"])
        self.assertEqual(
            [
                "common.protected_spans",
                "common.evidence_policy",
                "scene.architecture_design",
                "common.quality_gate_h1_h6",
            ],
            decision["load_contracts"],
        )
        self.assertEqual([], decision["pending_confirmations"])
        self.assertEqual([], decision["blockers"])

    def test_insufficient_input_returns_unknown_and_candidates_without_guessing(self):
        result = self.run_decision(self.fixture["cases"][1]["request"])
        decision = result["decision"]

        self.assertEqual("unknown", decision["business_domain"]["value"])
        self.assertEqual("unclear", decision["business_domain"]["confidence"])
        self.assertEqual(
            ["engineering_construction"],
            [
                candidate["value"]
                for candidate in decision["business_domain"]["candidates"]
            ],
        )
        self.assertEqual("unknown", decision["material_subtype"]["value"])
        self.assertEqual("unclear", decision["material_subtype"]["confidence"])
        self.assertIn("business_domain", decision["pending_confirmations"])
        self.assertIn("material_subtype", decision["pending_confirmations"])
        self.assertEqual("conservative_audit", decision["processing_mode"])
        self.assertEqual([], decision["blockers"])

    def test_fixture_is_deterministic_and_not_model_evidence(self):
        self.assertEqual(
            "deterministic-synthetic-fixture", self.fixture["evidence_type"]
        )
        self.assertFalse(self.fixture["model_execution"])
        self.assertIn("不代表真实模型运行通过率", self.fixture["statement"])

    def test_normalized_view_must_explicitly_disclaim_formal_status(self):
        request = deepcopy(self.fixture["cases"][0]["request"])
        del request["material_view"]["is_formal_material"]

        completed = self.run_raw(request)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("invalid_request", error["error"])
        self.assertIn("不是新的正式材料", error["message"])

    def test_normalized_view_rejects_locator_without_a_usable_value(self):
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["material_view"]["segments"][0]["locator"] = {"page": None}

        completed = self.run_raw(request)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("invalid_request", error["error"])
        self.assertIn("最小定位", error["message"])

    def test_normalized_view_accepts_a_later_located_segment(self):
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["material_view"]["segments"].insert(
            0, {"text": "封面未提供页码或章节号。"}
        )

        result = self.run_decision(request)

        self.assertEqual(
            {"section": "5.2", "page": 17},
            result["material_view"]["locator"],
        )

    def test_non_review_task_does_not_claim_basic_support(self):
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["task"].update(
            {
                "instruction": "新建一份初步设计说明书。",
                "mode": "create",
                "scope": "document",
            }
        )

        decision = self.run_decision(request)["decision"]

        self.assertEqual(
            "engineering_construction", decision["business_domain"]["value"]
        )
        self.assertEqual("recognition_coverage", decision["support_level"])
        self.assertEqual("conservative_audit", decision["processing_mode"])
        self.assertIn("task_mode_support", decision["pending_confirmations"])

    def test_negated_preliminary_design_signal_stays_unclear(self):
        request = deepcopy(self.fixture["cases"][1]["request"])
        request["task"]["instruction"] = (
            "审阅这份材料；这不是初步设计，文种尚未确认。"
        )

        decision = self.run_decision(request)["decision"]

        self.assertEqual("unknown", decision["business_domain"]["value"])
        self.assertEqual("unclear", decision["material_subtype"]["confidence"])
        self.assertEqual("conservative_audit", decision["processing_mode"])
        self.assertIn("material_subtype", decision["pending_confirmations"])

    def test_semantic_negation_of_preliminary_design_stays_unclear(self):
        request = deepcopy(self.fixture["cases"][1]["request"])
        request["task"]["instruction"] = (
            "审阅这份材料；该材料不属于初步设计，文种未确认。"
        )

        decision = self.run_decision(request)["decision"]

        self.assertEqual("unknown", decision["business_domain"]["value"])
        self.assertEqual("unclear", decision["material_subtype"]["confidence"])
        self.assertEqual("conservative_audit", decision["processing_mode"])

    def test_unconfirmed_parameter_does_not_negate_document_classification(self):
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["task"]["instruction"] = (
            "审阅初步设计中尚未确认的参数，只标出问题。"
        )

        decision = self.run_decision(request)["decision"]

        self.assertEqual(
            "engineering_construction", decision["business_domain"]["value"]
        )
        self.assertEqual("explicit", decision["material_subtype"]["confidence"])
        self.assertEqual("quick_path", decision["processing_mode"])


if __name__ == "__main__":
    unittest.main()
