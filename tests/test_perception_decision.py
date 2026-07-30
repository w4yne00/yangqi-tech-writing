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

    def run_statement_force_case(self, case_id):
        case = next(
            item
            for item in self.fixture["statement_force_cases"]
            if item["case_id"] == case_id
        )
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["claims"] = deepcopy(case["claims"])
        return self.run_decision(request)["decision"]

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
                "common.statement_force_policy",
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

    def test_all_statement_forces_remain_distinct_from_evidence_status(self):
        decision = self.run_statement_force_case(
            "FOUNDATION-06-POSITIVE-STATEMENT-FORCES"
        )

        claim_decisions = decision["claim_decisions"]
        self.assertEqual(
            [
                "assumption",
                "professional_judgment",
                "recommended_solution",
                "approved_boundary",
                "contractual_commitment",
                "implementation_fact",
                "acceptance_conclusion",
            ],
            [claim["allowed_statement_force"] for claim in claim_decisions],
        )
        self.assertEqual(
            [
                "OPINION",
                "OPINION",
                "SUPPORTED",
                "SUPPORTED",
                "SUPPORTED",
                "SUPPORTED",
                "SUPPORTED",
            ],
            [claim["evidence_status"] for claim in claim_decisions],
        )
        self.assertTrue(
            all(claim["action"] == "preserve" for claim in claim_decisions)
        )

    def test_supported_recommendation_is_not_strengthened_by_genre_conversion(self):
        decision = self.run_statement_force_case(
            "FOUNDATION-06-STRENGTHENING-NEAR-MISS"
        )

        claim = decision["claim_decisions"][0]
        self.assertEqual("SUPPORTED", claim["evidence_status"])
        self.assertEqual("recommended_solution", claim["source_statement_force"])
        self.assertEqual("approved_boundary", claim["requested_statement_force"])
        self.assertEqual("recommended_solution", claim["allowed_statement_force"])
        self.assertEqual("preserve_source_force", claim["action"])
        self.assertEqual([], decision["blockers"])

    def test_implementation_fact_is_not_weakened_by_genre_conversion(self):
        decision = self.run_statement_force_case(
            "FOUNDATION-06-WEAKENING-NEAR-MISS"
        )

        claim = decision["claim_decisions"][0]
        self.assertEqual("implementation_fact", claim["source_statement_force"])
        self.assertEqual("recommended_solution", claim["requested_statement_force"])
        self.assertEqual("implementation_fact", claim["allowed_statement_force"])
        self.assertEqual("preserve_source_force", claim["action"])

    def test_unclear_statement_force_requires_confirmation_and_uses_assumption(self):
        decision = self.run_statement_force_case(
            "FOUNDATION-06-UNCLEAR-FORCE"
        )

        claim = decision["claim_decisions"][0]
        self.assertEqual("NEEDS_USER_CONFIRMATION", claim["evidence_status"])
        self.assertEqual("unknown", claim["source_statement_force"])
        self.assertEqual("assumption", claim["allowed_statement_force"])
        self.assertEqual("confirm_and_use_lower_force", claim["action"])
        self.assertIn("statement_force:F06-UNCLEAR-001", decision["pending_confirmations"])
        self.assertIn("claim:F06-UNCLEAR-001", decision["blockers"])

    def test_unsupported_high_effect_claim_keeps_force_but_blocks_finalizing(self):
        decision = self.run_statement_force_case(
            "FOUNDATION-06-UNSUPPORTED-HIGH-EFFECT"
        )

        claim = decision["claim_decisions"][0]
        self.assertEqual("UNSUPPORTED", claim["evidence_status"])
        self.assertEqual("implementation_fact", claim["source_statement_force"])
        self.assertEqual("implementation_fact", claim["allowed_statement_force"])
        self.assertEqual("require_source", claim["action"])
        self.assertIn("claim:F06-UNSUPPORTED-001", decision["blockers"])

    def test_opinion_cannot_be_preserved_as_a_formal_effect_claim(self):
        decision = self.run_statement_force_case(
            "FOUNDATION-06-OPINION-FORCE-CONFLICT"
        )

        claim = decision["claim_decisions"][0]
        self.assertEqual("OPINION", claim["evidence_status"])
        self.assertEqual("acceptance_conclusion", claim["source_statement_force"])
        self.assertIsNone(claim["allowed_statement_force"])
        self.assertEqual("confirm_evidence_force_alignment", claim["action"])
        self.assertIn(
            "evidence_force:F06-OPINION-CONFLICT-001",
            decision["pending_confirmations"],
        )
        self.assertIn("claim:F06-OPINION-CONFLICT-001", decision["blockers"])

    def test_supported_downstream_risk_is_not_converted_to_implementation_fact(self):
        decision = self.run_statement_force_case(
            "FOUNDATION-06-CAUSAL-RISK-BOUNDARY"
        )

        claim = decision["claim_decisions"][0]
        self.assertEqual("SUPPORTED", claim["evidence_status"])
        self.assertEqual("professional_judgment", claim["source_statement_force"])
        self.assertEqual("implementation_fact", claim["requested_statement_force"])
        self.assertEqual("professional_judgment", claim["allowed_statement_force"])
        self.assertEqual("preserve_source_force", claim["action"])

    def test_conflicted_claim_is_blocked_without_force_substitution(self):
        decision = self.run_statement_force_case("FOUNDATION-06-CONFLICT")

        claim = decision["claim_decisions"][0]
        self.assertEqual("CONTRADICTED", claim["evidence_status"])
        self.assertEqual("approved_boundary", claim["source_statement_force"])
        self.assertIsNone(claim["allowed_statement_force"])
        self.assertEqual("block_conflict", claim["action"])
        self.assertIn("claim:F06-CONFLICT-001", decision["blockers"])

    def test_conflicted_unknown_force_still_reports_force_confirmation(self):
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["claims"] = [
            {
                "claim_id": "F06-CONFLICT-UNKNOWN",
                "text": "本期建设范围包括灾备中心。",
                "evidence_status": "CONTRADICTED",
                "statement_force": "unknown",
                "conflict_ref": "两份材料的范围不一致",
            }
        ]

        decision = self.run_decision(request)["decision"]

        claim = decision["claim_decisions"][0]
        self.assertIsNone(claim["allowed_statement_force"])
        self.assertEqual("block_conflict", claim["action"])
        self.assertIn(
            "statement_force:F06-CONFLICT-UNKNOWN",
            decision["pending_confirmations"],
        )

    def test_unknown_force_without_conversion_target_uses_conservative_default(self):
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["claims"] = [
            {
                "claim_id": "F06-UNCLEAR-002",
                "text": "本期建设范围包括灾备中心。",
                "evidence_status": "NEEDS_USER_CONFIRMATION",
                "statement_force": "unknown",
            }
        ]

        decision = self.run_decision(request)["decision"]

        claim = decision["claim_decisions"][0]
        self.assertEqual("unknown", claim["requested_statement_force"])
        self.assertEqual("assumption", claim["allowed_statement_force"])

    def test_supported_claim_rejects_non_text_source_reference(self):
        for invalid_source_ref in (None, False, 7):
            with self.subTest(source_ref=invalid_source_ref):
                request = deepcopy(self.fixture["cases"][0]["request"])
                request["claims"] = [
                    {
                        "claim_id": "F06-INVALID-SOURCE",
                        "text": "建议分两期建设。",
                        "evidence_status": "SUPPORTED",
                        "statement_force": "recommended_solution",
                        "source_ref": invalid_source_ref,
                    }
                ]

                completed = self.run_raw(request)

                self.assertEqual(1, completed.returncode)
                error = json.loads(completed.stderr)
                self.assertEqual("invalid_request", error["error"])
                self.assertIn("source_ref", error["message"])


if __name__ == "__main__":
    unittest.main()
