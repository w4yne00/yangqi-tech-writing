from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from scripts.perception_decision import build_perception_decision


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/perception_decision.py"
FIXTURE = ROOT / "tests/fixtures/perception-decision-cases.json"


class WritingPreparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def run_decision(self, request):
        completed = subprocess.run(
            [sys.executable, str(SCRIPT), "-"],
            input=json.dumps(request, ensure_ascii=False),
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertEqual(0, completed.returncode, completed.stderr)
        return json.loads(completed.stdout)["decision"]

    def test_complete_document_creation_returns_confirmable_preparation_sheet(self):
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["task"] = {
            "instruction": "新建一份完整的初步设计说明书。",
            "mode": "create",
            "scope": "document",
        }
        request["claims"] = [
            {
                "claim_id": "F07-FACT-001",
                "text": "本期建设范围包括集团总部。",
                "evidence_status": "SUPPORTED",
                "statement_force": "approved_boundary",
                "source_ref": "批复文件第3条",
            },
            {
                "claim_id": "F07-ASSUMPTION-001",
                "text": "假设现有机房具备扩容条件。",
                "evidence_status": "NEEDS_USER_CONFIRMATION",
                "statement_force": "assumption",
            },
            {
                "claim_id": "F07-JUDGMENT-001",
                "text": "建议采用双节点部署方案。",
                "evidence_status": "SUPPORTED",
                "statement_force": "recommended_solution",
                "source_ref": "方案比选表2",
            },
        ]

        decision = self.run_decision(request)

        self.assertEqual("two_stage", decision["processing_mode"])
        sheet = decision["writing_preparation_sheet"]
        self.assertEqual("preparation", sheet["current_stage"])
        self.assertTrue(sheet["confirmation_required"])
        self.assertEqual(
            "draft_after_user_confirmation",
            sheet["next_stage"],
        )
        self.assertEqual(
            "SYNTHETIC-SOURCE-001",
            sheet["material_inventory"][0]["source_id"],
        )
        self.assertFalse(
            sheet["material_inventory"][0]["is_formal_material"]
        )
        self.assertEqual(
            "engineering_construction",
            sheet["perception_dimensions"]["business_domain"]["value"],
        )
        self.assertEqual(
            ["F07-FACT-001", "F07-JUDGMENT-001"],
            [
                item["claim_id"]
                for item in sheet["facts_and_judgments"]["confirmed"]
            ],
        )
        self.assertEqual(
            ["fact", "judgment"],
            [
                item["kind"]
                for item in sheet["facts_and_judgments"]["confirmed"]
            ],
        )
        self.assertEqual(
            ["F07-ASSUMPTION-001"],
            [
                item["claim_id"]
                for item in sheet["assumptions"]["requires_user_confirmation"]
            ],
        )
        self.assertIn(
            "evidence:F07-ASSUMPTION-001",
            [
                item["item_id"]
                for item in sheet["confirmation_boundary"][
                    "requires_user_confirmation"
                ]
            ],
        )
        self.assertEqual(
            decision["load_contracts"],
            sheet["proposed_contracts"],
        )
        self.assertEqual(
            ["批复文件第3条", "方案比选表2"],
            sheet["traceability_summary"]["claim_source_refs"],
        )
        for hidden_field in (
            "reasoning",
            "chain_of_thought",
            "internal_analysis",
        ):
            self.assertNotIn(hidden_field, sheet)

    def test_high_risk_material_integration_returns_traceable_preparation_sheet(self):
        request = deepcopy(self.fixture["cases"][0]["request"])
        material_set_case = next(
            item
            for item in self.fixture["material_set_cases"]
            if item["case_id"] == "FOUNDATION-08-RELATION-TYPES"
        )
        request["material_set"] = deepcopy(
            material_set_case["material_set"]
        )

        decision = self.run_decision(request)

        self.assertEqual("two_stage", decision["processing_mode"])
        sheet = decision["writing_preparation_sheet"]
        self.assertEqual(
            decision["material_set_review"]["materials"],
            sheet["material_inventory"][1:],
        )
        self.assertEqual(
            decision["material_set_review"]["relationships"],
            sheet["material_relationships"],
        )
        self.assertEqual(
            decision["material_set_review"]["control_materials"],
            sheet["control_materials"],
        )
        self.assertEqual(
            decision["material_set_review"]["conflicts"],
            sheet["conflicts"],
        )
        self.assertIn(
            "material_relation:F08-R-CONFLICTS",
            sheet["pending_confirmations"],
        )
        self.assertIn(
            "material_relation:F08-R-UNCLEAR",
            sheet["blockers"],
        )
        self.assertEqual(
            [
                relationship["relation_id"]
                for relationship in decision["material_set_review"][
                    "relationships"
                ]
            ],
            sheet["traceability_summary"]["relationship_ids"],
        )
        self.assertEqual(
            [
                "SYNTHETIC-SOURCE-001",
                "F08-REQUIREMENT",
                "F08-DESIGN",
                "F08-IMPLEMENTATION",
                "F08-ACCEPTANCE",
            ],
            sheet["traceability_summary"]["source_ids"],
        )
        self.assertIn(
            "common.material_set_review",
            sheet["proposed_contracts"],
        )

    def test_bounded_local_tasks_use_quick_path_without_skipping_hard_gates(self):
        for mode in ("rewrite", "review", "annotation"):
            with self.subTest(mode=mode):
                request = deepcopy(self.fixture["cases"][0]["request"])
                request["task"] = {
                    "instruction": "局部处理初步设计第5.2节，控制边界明确。",
                    "mode": mode,
                    "scope": "local",
                }

                decision = self.run_decision(request)

                self.assertEqual(mode, decision["task_mode"])
                self.assertEqual("quick_path", decision["processing_mode"])
                self.assertNotIn("writing_preparation_sheet", decision)
                for contract in (
                    "common.protected_spans",
                    "common.evidence_policy",
                    "common.statement_force_policy",
                    "common.quality_gate_h1_h6",
                ):
                    self.assertIn(contract, decision["load_contracts"])

    def test_local_scope_with_unresolved_formal_claim_is_not_a_quick_path(self):
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["task"] = {
            "instruction": "局部改写初步设计第5.2节。",
            "mode": "rewrite",
            "scope": "local",
        }
        request["claims"] = [
            {
                "claim_id": "F07-HIGH-RISK-NEAR-MISS",
                "text": "平台已完成全部部署。",
                "evidence_status": "UNSUPPORTED",
                "statement_force": "implementation_fact",
            }
        ]

        decision = self.run_decision(request)

        self.assertEqual("conservative_audit", decision["processing_mode"])
        self.assertIn(
            "claim:F07-HIGH-RISK-NEAR-MISS",
            decision["blockers"],
        )
        self.assertNotIn("writing_preparation_sheet", decision)

    def test_two_stage_contract_does_not_leak_into_a_later_non_two_stage_task(self):
        create_request = deepcopy(self.fixture["cases"][0]["request"])
        create_request["task"] = {
            "instruction": "新建一份完整的初步设计说明书。",
            "mode": "create",
            "scope": "document",
        }
        later_request = deepcopy(self.fixture["cases"][1]["request"])

        create_decision = build_perception_decision(
            create_request
        )["decision"]
        later_decision = build_perception_decision(
            later_request
        )["decision"]

        self.assertIn(
            "common.writing_preparation",
            create_decision["load_contracts"],
        )
        self.assertNotIn(
            "common.writing_preparation",
            later_decision["load_contracts"],
        )

    def test_unrecognized_document_creation_is_not_forced_into_two_stage(self):
        request = deepcopy(self.fixture["cases"][1]["request"])
        request["task"] = {
            "instruction": "新建一份完整会议纪要。",
            "mode": "create",
            "scope": "document",
        }
        request["material_view"]["title"] = "会议记录"
        request["material_view"]["segments"][0]["text"] = "记录会议讨论事项。"

        decision = self.run_decision(request)

        self.assertEqual(
            "conservative_audit",
            decision["processing_mode"],
        )
        self.assertNotIn("writing_preparation_sheet", decision)

    def test_every_unconfirmed_claim_is_exposed_in_confirmation_boundary(self):
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["task"] = {
            "instruction": "新建一份完整的初步设计说明书。",
            "mode": "create",
            "scope": "document",
        }
        request["claims"] = [
            {
                "claim_id": "F07-UNSUPPORTED-JUDGMENT",
                "text": "建议采用双节点部署方案。",
                "evidence_status": "UNSUPPORTED",
                "statement_force": "recommended_solution",
            },
            {
                "claim_id": "F07-SUPPORTED-FACT",
                "text": "本期建设范围包括集团总部。",
                "evidence_status": "SUPPORTED",
                "statement_force": "approved_boundary",
                "source_ref": "批复文件第3条",
            }
        ]

        sheet = self.run_decision(request)["writing_preparation_sheet"]

        self.assertIn(
            "claim:F07-UNSUPPORTED-JUDGMENT",
            sheet["pending_confirmations"],
        )
        confirmation_items = {
            item["item_id"]: item
            for item in sheet["confirmation_boundary"][
                "requires_user_confirmation"
            ]
        }
        self.assertEqual(
            "claim",
            confirmation_items[
                "claim:F07-UNSUPPORTED-JUDGMENT"
            ]["category"],
        )
        confirmed_categories = {
            item["category"]
            for item in sheet["confirmation_boundary"]["confirmed"]
        }
        for category in (
            "task",
            "material",
            "perception",
            "claim",
        ):
            self.assertIn(category, confirmed_categories)


if __name__ == "__main__":
    unittest.main()
