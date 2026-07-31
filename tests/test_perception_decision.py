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

    def run_material_set_case(self, case_id):
        case = next(
            item
            for item in self.fixture["material_set_cases"]
            if item["case_id"] == case_id
        )
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["material_set"] = deepcopy(case["material_set"])
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
        self.assertEqual("two_stage", decision["processing_mode"])
        self.assertIn("writing_preparation_sheet", decision)
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

    def test_material_set_preserves_all_supported_relationship_types(self):
        decision = self.run_material_set_case(
            "FOUNDATION-08-RELATION-TYPES"
        )

        review = decision["material_set_review"]
        self.assertEqual("material_set", review["mode"])
        self.assertEqual(
            "two_stage",
            decision["processing_mode"],
        )
        self.assertIn("writing_preparation_sheet", decision)
        self.assertIn(
            "common.material_set_review",
            decision["load_contracts"],
        )
        self.assertEqual(
            {
                "material_id": "F08-REQUIREMENT",
                "title": "批复材料",
                "version": "1.0",
                "material_subtype": "approval",
                "status": "approved",
                "date": "2026-01-10",
                "user_designated_control": False,
            },
            review["materials"][0],
        )
        self.assertEqual(
            [
                "governs",
                "derives_from",
                "supersedes",
                "implements",
                "verifies",
                "conflicts_with",
                "unclear",
            ],
            [
                relationship["relation_type"]
                for relationship in review["relationships"]
            ],
        )
        for relation_id in ("F08-R-CONFLICTS", "F08-R-UNCLEAR"):
            item = "material_relation:{}".format(relation_id)
            self.assertIn(item, decision["pending_confirmations"])
            self.assertIn(item, decision["blockers"])
        incomplete_conflict = next(
            conflict
            for conflict in review["conflicts"]
            if conflict["conflict_id"] == "relation:F08-R-CONFLICTS"
        )
        self.assertEqual("unclear", incomplete_conflict["dimension"])
        self.assertEqual(
            "范围口径不一致",
            incomplete_conflict["difference"],
        )
        self.assertEqual("not_provided", incomplete_conflict["impact"])
        self.assertEqual(
            "provide_conflict_dimension_and_impact",
            incomplete_conflict["pending_confirmation"],
        )

    def test_newer_material_date_does_not_create_supersedes(self):
        decision = self.run_material_set_case(
            "FOUNDATION-08-NEWER-DATE-IS-NOT-SUPERSEDES"
        )

        review = decision["material_set_review"]
        self.assertEqual(
            "explicit_relationships_only",
            review["precedence_policy"],
        )
        self.assertNotIn(
            "supersedes",
            [
                relationship["relation_type"]
                for relationship in review["relationships"]
            ],
        )
        self.assertEqual("blocked", review["review_status"])
        self.assertIn(
            "material_set:missing_relationships",
            decision["blockers"],
        )

    def test_explicit_formal_and_user_control_bases_enter_decision(self):
        decision = self.run_material_set_case(
            "FOUNDATION-08-RELATION-TYPES"
        )

        control_materials = {
            item["material_id"]: item["control_bases"]
            for item in decision["material_set_review"]["control_materials"]
        }
        self.assertIn(
            "formal_status:approved",
            control_materials["F08-REQUIREMENT"],
        )
        self.assertIn(
            "relation:governs:F08-R-GOVERNS",
            control_materials["F08-REQUIREMENT"],
        )
        self.assertEqual(
            ["formal_status:signed"],
            control_materials["F08-DESIGN"],
        )
        self.assertEqual(
            ["user_designated"],
            control_materials["F08-IMPLEMENTATION"],
        )

    def test_all_formal_conflict_dimensions_block_without_adjudication(self):
        decision = self.run_material_set_case(
            "FOUNDATION-08-CONFLICT-DIMENSIONS"
        )

        review = decision["material_set_review"]
        conflicts = review["conflicts"]
        self.assertEqual(
            [
                "scope",
                "quantity",
                "parameter",
                "responsibility",
                "time",
                "conclusion",
                "statement_force",
            ],
            [conflict["dimension"] for conflict in conflicts],
        )
        self.assertEqual("blocked", review["review_status"])
        for conflict in conflicts:
            self.assertTrue(conflict["difference"])
            self.assertTrue(conflict["impact"])
            self.assertTrue(conflict["pending_confirmation"])
            for prohibited in ("resolution", "winner", "legal_effect"):
                self.assertNotIn(prohibited, conflict)
            self.assertIn(
                "material_conflict:{}".format(conflict["conflict_id"]),
                decision["blockers"],
            )

    def test_each_conflict_relation_requires_its_own_structured_details(self):
        case = next(
            item
            for item in self.fixture["material_set_cases"]
            if item["case_id"] == "FOUNDATION-08-CONFLICT-DIMENSIONS"
        )
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["material_set"] = deepcopy(case["material_set"])
        request["material_set"]["relations"].append(
            {
                "relation_id": "F08-R-CONFLICT-SECOND",
                "from_material_id": "F08-CONFLICT-LEFT",
                "to_material_id": "F08-CONFLICT-RIGHT",
                "relation_type": "conflicts_with",
                "basis": "同一材料对另有参数口径冲突",
            }
        )

        decision = self.run_decision(request)["decision"]

        incomplete_conflict = next(
            conflict
            for conflict in decision["material_set_review"]["conflicts"]
            if conflict["conflict_id"]
            == "relation:F08-R-CONFLICT-SECOND"
        )
        self.assertEqual(
            "同一材料对另有参数口径冲突",
            incomplete_conflict["difference"],
        )
        self.assertEqual("not_provided", incomplete_conflict["impact"])

    def test_missing_upstream_blocks_cross_stage_consistency_claim(self):
        decision = self.run_material_set_case(
            "FOUNDATION-08-MISSING-UPSTREAM"
        )

        review = decision["material_set_review"]
        self.assertEqual(
            {
                "status": "not_verifiable",
                "reason": "missing_upstream_materials",
            },
            review["cross_stage_consistency"],
        )
        self.assertEqual("not_completed", review["completion_claim"])
        self.assertEqual("blocked", review["review_status"])
        self.assertIn("material_set:missing_upstream", decision["blockers"])

    def test_single_material_does_not_claim_material_set_review_complete(self):
        decision = self.run_decision(
            self.fixture["cases"][0]["request"]
        )["decision"]

        review = decision["material_set_review"]
        self.assertEqual("single_material", review["mode"])
        self.assertEqual("single_material_only", review["review_status"])
        self.assertEqual(
            "not_verifiable",
            review["cross_stage_consistency"]["status"],
        )
        self.assertEqual("not_completed", review["completion_claim"])
        self.assertNotIn("material_set:missing_upstream", decision["blockers"])

    def test_one_item_material_set_cannot_claim_cross_stage_reviewable(self):
        case = next(
            item
            for item in self.fixture["material_set_cases"]
            if item["case_id"] == "FOUNDATION-08-MISSING-UPSTREAM"
        )
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["material_set"] = deepcopy(case["material_set"])
        request["material_set"]["upstream_materials_complete"] = True

        decision = self.run_decision(request)["decision"]

        review = decision["material_set_review"]
        self.assertEqual(
            {
                "status": "not_verifiable",
                "reason": "insufficient_materials_for_cross_stage_review",
            },
            review["cross_stage_consistency"],
        )
        self.assertIn(
            "material_set:insufficient_materials",
            decision["blockers"],
        )

    def test_each_material_requires_an_explicit_cross_material_relationship(self):
        case = next(
            item
            for item in self.fixture["material_set_cases"]
            if item["case_id"] == "FOUNDATION-08-NEWER-DATE-IS-NOT-SUPERSEDES"
        )
        material_set = deepcopy(case["material_set"])
        material_set["materials"].append(
            {
                "material_id": "F08-ORPHAN",
                "title": "未声明关系的实施记录",
                "version": "1.0",
                "material_subtype": "implementation_record",
                "status": "draft",
            }
        )
        material_set["relations"] = [
            {
                "relation_id": "F08-R-PARTIAL",
                "from_material_id": "F08-NEWER-DRAFT",
                "to_material_id": "F08-OLDER-APPROVED",
                "relation_type": "derives_from",
                "basis": "工作稿引用批复材料",
            }
        ]
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["material_set"] = material_set

        decision = self.run_decision(request)["decision"]

        review = decision["material_set_review"]
        self.assertEqual("blocked", review["review_status"])
        self.assertIn(
            "material_set:unrelated_material:F08-ORPHAN",
            decision["pending_confirmations"],
        )
        self.assertIn(
            "material_set:unrelated_material:F08-ORPHAN",
            decision["blockers"],
        )

        self_relation_request = deepcopy(request)
        self_relation_request["material_set"]["materials"] = (
            self_relation_request["material_set"]["materials"][:2]
        )
        self_relation_request["material_set"]["relations"] = [
            {
                "relation_id": "F08-R-SELF",
                "from_material_id": "F08-OLDER-APPROVED",
                "to_material_id": "F08-OLDER-APPROVED",
                "relation_type": "governs",
                "basis": "材料不能以自关联证明跨材料关系",
            }
        ]

        self_relation_decision = self.run_decision(
            self_relation_request
        )["decision"]
        approved_control = next(
            item
            for item in self_relation_decision["material_set_review"][
                "control_materials"
            ]
            if item["material_id"] == "F08-OLDER-APPROVED"
        )
        self.assertNotIn(
            "relation:governs:F08-R-SELF",
            approved_control["control_bases"],
        )
        for material_id in ("F08-OLDER-APPROVED", "F08-NEWER-DRAFT"):
            self.assertIn(
                "material_set:unrelated_material:{}".format(material_id),
                self_relation_decision["blockers"],
            )

    def test_material_set_rejects_unsupported_relation_and_conflict_dimension(self):
        relation_case = next(
            item
            for item in self.fixture["material_set_cases"]
            if item["case_id"] == "FOUNDATION-08-NEWER-DATE-IS-NOT-SUPERSEDES"
        )
        conflict_case = next(
            item
            for item in self.fixture["material_set_cases"]
            if item["case_id"] == "FOUNDATION-08-CONFLICT-DIMENSIONS"
        )
        invalid_inputs = []

        invalid_relation = deepcopy(relation_case["material_set"])
        invalid_relation["relations"] = [
            {
                "relation_id": "F08-R-INVALID",
                "from_material_id": "F08-OLDER-APPROVED",
                "to_material_id": "F08-NEWER-DRAFT",
                "relation_type": "newer_than",
                "basis": "仅有文件日期",
            }
        ]
        invalid_inputs.append((invalid_relation, "relation_type"))

        invalid_conflict = deepcopy(conflict_case["material_set"])
        invalid_conflict["conflicts"][0]["dimension"] = "legal_effect"
        invalid_inputs.append((invalid_conflict, "dimension"))

        invalid_status = deepcopy(relation_case["material_set"])
        invalid_status["materials"][0]["status"] = "已批准"
        invalid_inputs.append((invalid_status, "status"))

        for material_set, expected_field in invalid_inputs:
            with self.subTest(expected_field=expected_field):
                request = deepcopy(self.fixture["cases"][0]["request"])
                request["material_set"] = material_set

                completed = self.run_raw(request)

                self.assertEqual(1, completed.returncode)
                error = json.loads(completed.stderr)
                self.assertEqual("invalid_request", error["error"])
                self.assertIn(expected_field, error["message"])

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
