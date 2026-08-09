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

    def run_engineering_case(self, case_id):
        case = next(
            item
            for item in self.fixture["engineering_construction_cases"]
            if item["case_id"] == case_id
        )
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["task"]["instruction"] = case["instruction"]
        request["material_view"]["title"] = case["title"]
        request["material_view"]["segments"][0]["text"] = (
            "本合成片段只提供材料识别所需的最小信息。"
        )
        return case, self.run_decision(request)["decision"]

    def run_research_case(self, case_id):
        case = next(
            item
            for item in self.fixture["research_project_cases"]
            if item["case_id"] == case_id
        )
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["task"]["instruction"] = case["instruction"]
        request["material_view"]["title"] = case["title"]
        request["material_view"]["segments"][0]["text"] = (
            "本合成片段只提供材料识别所需的最小信息。"
        )
        return case, self.run_decision(request)["decision"]

    def run_governance_case(self, case_id):
        case = next(
            item
            for item in self.fixture["governance_operation_cases"]
            if item["case_id"] == case_id
        )
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["task"]["instruction"] = case["instruction"]
        request["material_view"]["title"] = case["title"]
        request["material_view"]["segments"][0]["text"] = (
            "本合成片段只提供材料识别所需的最小信息。"
        )
        return case, self.run_decision(request)["decision"]

    def test_management_policy_uses_governance_domain_and_policy_contract(self):
        case, decision = self.run_governance_case(
            "FOUNDATION-04-MANAGEMENT-POLICY"
        )

        self.assertEqual(
            "governance_operation", decision["business_domain"]["value"]
        )
        for dimension in (
            "lifecycle_position",
            "document_scene",
            "material_subtype",
        ):
            self.assertEqual(
                case["expected"][dimension], decision[dimension]["value"]
            )
            self.assertEqual("explicit", decision[dimension]["confidence"])
        self.assertEqual("basic_support", decision["support_level"])
        self.assertEqual("quick_path", decision["processing_mode"])
        self.assertEqual(
            [
                "common.protected_spans",
                "common.evidence_policy",
                "common.statement_force_policy",
                "scene.security_policy",
                "common.quality_gate_h1_h6",
            ],
            decision["load_contracts"],
        )

    def test_governance_catalog_preserves_lifecycle_scene_and_subtype(self):
        for case in self.fixture["governance_operation_cases"]:
            with self.subTest(case_id=case["case_id"]):
                _, decision = self.run_governance_case(case["case_id"])

                self.assertEqual(
                    "governance_operation",
                    decision["business_domain"]["value"],
                )
                for dimension in (
                    "lifecycle_position",
                    "document_scene",
                    "material_subtype",
                ):
                    self.assertEqual(
                        case["expected"][dimension],
                        decision[dimension]["value"],
                    )
                self.assertEqual(
                    "basic_support", decision["support_level"]
                )
                self.assertEqual("quick_path", decision["processing_mode"])
                self.assertNotIn(
                    "deep_support",
                    json.dumps(decision, ensure_ascii=False),
                )

    def test_governance_report_keeps_domain_and_presentation_scene(self):
        _, decision = self.run_governance_case(
            "FOUNDATION-04-GOVERNANCE-REPORT"
        )

        self.assertEqual(
            "governance_operation", decision["business_domain"]["value"]
        )
        self.assertEqual(
            "inspection_evaluation",
            decision["lifecycle_position"]["value"],
        )
        self.assertEqual("presentation", decision["document_scene"]["value"])
        self.assertEqual(
            "governance_report", decision["material_subtype"]["value"]
        )
        self.assertIn("scene.presentation", decision["load_contracts"])
        self.assertNotIn("scene.security_policy", decision["load_contracts"])

    def test_unclear_governance_material_uses_conservative_base_contract(self):
        request = deepcopy(self.fixture["cases"][1]["request"])
        request["task"]["instruction"] = (
            "审阅这份治理运行材料；具体类型、组织职责和制度效力均未确认。"
        )
        request["material_view"]["title"] = "治理运行材料"
        request["material_view"]["segments"][0]["text"] = (
            "本材料未提供能够确认生命周期、文种或材料子类型的信息。"
        )

        decision = self.run_decision(request)["decision"]

        self.assertEqual("unknown", decision["business_domain"]["value"])
        self.assertEqual(
            {"governance_operation"},
            {
                item["value"]
                for item in decision["business_domain"]["candidates"]
            },
        )
        self.assertEqual("unknown", decision["material_subtype"]["value"])
        self.assertEqual("recognition_coverage", decision["support_level"])
        self.assertEqual("conservative_audit", decision["processing_mode"])
        self.assertEqual(
            [
                "common.protected_spans",
                "common.evidence_policy",
                "common.statement_force_policy",
                "common.quality_gate_h1_h6",
            ],
            decision["load_contracts"],
        )
        self.assertEqual([], decision["claim_decisions"])
        self.assertNotIn(
            "approved_boundary",
            json.dumps(decision, ensure_ascii=False),
        )

    def test_recognized_governance_document_creation_uses_two_stage_only(self):
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["task"] = {
            "instruction": "新建一份完整的网络安全管理制度。",
            "mode": "create",
            "scope": "document",
        }
        request["material_view"]["title"] = "网络安全管理制度"
        request["material_view"]["segments"][0]["text"] = (
            "本合成片段只提供材料识别所需的最小信息。"
        )

        decision = self.run_decision(request)["decision"]

        self.assertEqual(
            "governance_operation", decision["business_domain"]["value"]
        )
        self.assertEqual(
            "management_policy", decision["material_subtype"]["value"]
        )
        self.assertEqual("recognition_coverage", decision["support_level"])
        self.assertEqual("two_stage", decision["processing_mode"])
        self.assertIn("writing_preparation_sheet", decision)
        self.assertIn(
            "common.writing_preparation", decision["load_contracts"]
        )
        self.assertNotIn("scene.security_policy", decision["load_contracts"])

    def test_research_application_uses_research_lifecycle(self):
        case, decision = self.run_research_case(
            "FOUNDATION-03-RESEARCH-APPLICATION"
        )

        self.assertEqual(
            "research_project", decision["business_domain"]["value"]
        )
        for dimension in (
            "lifecycle_position",
            "document_scene",
            "material_subtype",
        ):
            self.assertEqual(
                case["expected"][dimension], decision[dimension]["value"]
            )
            self.assertEqual("explicit", decision[dimension]["confidence"])
        self.assertEqual("basic_support", decision["support_level"])
        self.assertEqual("quick_path", decision["processing_mode"])
        self.assertIn("scene.feasibility_study", decision["load_contracts"])

    def test_research_catalog_preserves_lifecycle_scene_and_subtype(self):
        for case in self.fixture["research_project_cases"]:
            with self.subTest(case_id=case["case_id"]):
                _, decision = self.run_research_case(case["case_id"])

                self.assertEqual(
                    "research_project",
                    decision["business_domain"]["value"],
                )
                for dimension in (
                    "lifecycle_position",
                    "document_scene",
                    "material_subtype",
                ):
                    self.assertEqual(
                        case["expected"][dimension],
                        decision[dimension]["value"],
                    )
                self.assertEqual(
                    "basic_support", decision["support_level"]
                )
                self.assertEqual("quick_path", decision["processing_mode"])
                self.assertNotIn(
                    "deep_support",
                    json.dumps(decision, ensure_ascii=False),
                )

    def test_research_catalog_accepts_issue_terms_without_report_suffix(self):
        cases = (
            (
                "科研申报书",
                "application",
                "research_application",
            ),
            (
                "科研课题可研论证",
                "application",
                "research_feasibility_assessment",
            ),
            (
                "科研实施方案",
                "research_implementation",
                "research_implementation_plan",
            ),
            (
                "科研课题中期检查",
                "midterm_review",
                "research_interim_inspection",
            ),
        )

        for title, expected_lifecycle, expected_subtype in cases:
            with self.subTest(title=title):
                request = deepcopy(self.fixture["cases"][0]["request"])
                request["task"]["instruction"] = (
                    "审阅这份{}，只标出问题。".format(title)
                )
                request["material_view"]["title"] = title
                request["material_view"]["segments"][0]["text"] = (
                    "本合成片段只提供材料识别所需的最小信息。"
                )

                decision = self.run_decision(request)["decision"]

                self.assertEqual(
                    "research_project",
                    decision["business_domain"]["value"],
                )
                self.assertEqual(
                    expected_lifecycle,
                    decision["lifecycle_position"]["value"],
                )
                self.assertEqual(
                    expected_subtype,
                    decision["material_subtype"]["value"],
                )

    def test_research_context_combines_with_generic_document_titles(self):
        cases = (
            (
                "申报书",
                "application",
                "research_application",
            ),
            (
                "可研论证",
                "application",
                "research_feasibility_assessment",
            ),
            (
                "任务书",
                "task_agreement",
                "research_task_agreement",
            ),
            (
                "中期汇报",
                "midterm_review",
                "research_interim_report",
            ),
            (
                "中期检查",
                "midterm_review",
                "research_interim_inspection",
            ),
        )

        for title, expected_lifecycle, expected_subtype in cases:
            with self.subTest(title=title):
                request = deepcopy(self.fixture["cases"][0]["request"])
                request["task"]["instruction"] = (
                    "用户确认该材料属于科研课题，请审阅这份{}。".format(
                        title
                    )
                )
                request["material_view"]["title"] = title
                request["material_view"]["segments"][0]["text"] = (
                    "本合成片段只提供材料识别所需的最小信息。"
                )

                decision = self.run_decision(request)["decision"]

                self.assertEqual(
                    "research_project",
                    decision["business_domain"]["value"],
                )
                self.assertEqual(
                    expected_lifecycle,
                    decision["lifecycle_position"]["value"],
                )
                self.assertEqual(
                    expected_subtype,
                    decision["material_subtype"]["value"],
                )

    def test_recognized_research_document_creation_uses_two_stage_only(self):
        case = next(
            item
            for item in self.fixture["research_project_cases"]
            if item["case_id"] == "FOUNDATION-03-RESEARCH-TASK-AGREEMENT"
        )
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["task"] = {
            "instruction": "新建一份完整的科研课题任务书。",
            "mode": "create",
            "scope": "document",
        }
        request["material_view"]["title"] = case["title"]
        request["material_view"]["segments"][0]["text"] = (
            "本合成片段只提供材料识别所需的最小信息。"
        )

        decision = self.run_decision(request)["decision"]

        self.assertEqual(
            "research_project", decision["business_domain"]["value"]
        )
        self.assertEqual(
            "research_task_agreement",
            decision["material_subtype"]["value"],
        )
        self.assertEqual("recognition_coverage", decision["support_level"])
        self.assertEqual("two_stage", decision["processing_mode"])
        self.assertIn("writing_preparation_sheet", decision)
        self.assertIn(
            "common.writing_preparation", decision["load_contracts"]
        )
        self.assertNotIn("scene.technical_spec", decision["load_contracts"])

    def test_engineering_initiation_materials_keep_distinct_subtypes(self):
        for case_id in (
            "FOUNDATION-02-PROJECT-PROPOSAL",
            "FOUNDATION-02-FEASIBILITY-STUDY",
        ):
            with self.subTest(case_id=case_id):
                case, decision = self.run_engineering_case(case_id)

                self.assertEqual(
                    "engineering_construction",
                    decision["business_domain"]["value"],
                )
                for dimension in (
                    "lifecycle_position",
                    "document_scene",
                    "material_subtype",
                ):
                    self.assertEqual(
                        case["expected"][dimension],
                        decision[dimension]["value"],
                    )
                    self.assertEqual(
                        "explicit", decision[dimension]["confidence"]
                    )
                self.assertEqual("basic_support", decision["support_level"])
                self.assertEqual("quick_path", decision["processing_mode"])

    def test_engineering_design_near_misses_keep_distinct_subtypes(self):
        expected_subtypes = {
            "FOUNDATION-02-PRELIMINARY-DESIGN-NEAR-MISS":
                "preliminary_design",
            "FOUNDATION-02-DETAILED-DESIGN-NEAR-MISS": "detailed_design",
            "FOUNDATION-02-OVERALL-ARCHITECTURE": "overall_architecture",
        }

        actual_subtypes = {}
        for case_id, expected_subtype in expected_subtypes.items():
            with self.subTest(case_id=case_id):
                _, decision = self.run_engineering_case(case_id)
                actual_subtypes[case_id] = decision["material_subtype"]["value"]

                self.assertEqual(
                    "engineering_construction",
                    decision["business_domain"]["value"],
                )
                self.assertEqual(
                    "design", decision["lifecycle_position"]["value"]
                )
                self.assertEqual(
                    "architecture_design",
                    decision["document_scene"]["value"],
                )
                self.assertEqual(
                    expected_subtype,
                    decision["material_subtype"]["value"],
                )

        self.assertEqual(3, len(set(actual_subtypes.values())))

    def test_engineering_procurement_near_misses_load_distinct_scenes(self):
        expected_scenes = {
            "FOUNDATION-02-TECHNICAL-SPECIFICATION": (
                "technical_spec",
                "technical_specification",
                "scene.technical_spec",
            ),
            "FOUNDATION-02-BID-RESPONSE": (
                "bid_response",
                "bid_response",
                "scene.bid_response",
            ),
        }

        for case_id, (
            expected_scene,
            expected_subtype,
            expected_contract,
        ) in expected_scenes.items():
            with self.subTest(case_id=case_id):
                _, decision = self.run_engineering_case(case_id)

                self.assertEqual(
                    "procurement",
                    decision["lifecycle_position"]["value"],
                )
                self.assertEqual(
                    expected_scene, decision["document_scene"]["value"]
                )
                self.assertEqual(
                    expected_subtype,
                    decision["material_subtype"]["value"],
                )
                self.assertIn(expected_contract, decision["load_contracts"])
                self.assertNotIn(
                    "deep_support", json.dumps(decision, ensure_ascii=False)
                )

    def test_engineering_delivery_materials_preserve_lifecycle_and_genre(self):
        case_ids = (
            "FOUNDATION-02-ENGINEERING-IMPLEMENTATION-PLAN",
            "FOUNDATION-02-IMPLEMENTATION-RECORD",
            "FOUNDATION-02-STAGE-REPORT",
            "FOUNDATION-02-TRIAL-RUN-REPORT",
            "FOUNDATION-02-OPERATION-REPORT",
        )

        for case_id in case_ids:
            with self.subTest(case_id=case_id):
                case, decision = self.run_engineering_case(case_id)

                self.assertEqual(
                    "engineering_construction",
                    decision["business_domain"]["value"],
                )
                for dimension in (
                    "lifecycle_position",
                    "document_scene",
                    "material_subtype",
                ):
                    self.assertEqual(
                        case["expected"][dimension],
                        decision[dimension]["value"],
                    )
                self.assertEqual("basic_support", decision["support_level"])

    def test_engineering_acceptance_near_misses_keep_distinct_subtypes(self):
        case_ids = (
            "FOUNDATION-02-ACCEPTANCE-OUTLINE",
            "FOUNDATION-02-ACCEPTANCE-REPORT",
        )

        subtypes = []
        for case_id in case_ids:
            with self.subTest(case_id=case_id):
                case, decision = self.run_engineering_case(case_id)
                subtypes.append(decision["material_subtype"]["value"])

                self.assertEqual(
                    "acceptance",
                    decision["lifecycle_position"]["value"],
                )
                self.assertEqual(
                    "review_acceptance",
                    decision["document_scene"]["value"],
                )
                self.assertEqual(
                    case["expected"]["material_subtype"],
                    decision["material_subtype"]["value"],
                )
                self.assertIn(
                    "scene.review_acceptance",
                    decision["load_contracts"],
                )

        self.assertEqual(
            ["acceptance_outline", "acceptance_report"], subtypes
        )

    def test_ambiguous_engineering_materials_return_candidates_with_basis(self):
        cases = (
            (
                "设计材料",
                {
                    "preliminary_design",
                    "detailed_design",
                    "overall_architecture",
                },
            ),
            (
                "工程验收材料",
                {"acceptance_outline", "acceptance_report"},
            ),
            (
                "实施方案",
                {
                    "engineering_implementation_plan",
                    "research_implementation_plan",
                },
            ),
            (
                "阶段汇报",
                {"stage_report"},
            ),
            (
                "工程实施材料",
                {
                    "engineering_implementation_plan",
                    "implementation_record",
                },
            ),
            (
                "工程立项材料",
                {"project_proposal", "feasibility_study"},
            ),
            (
                "工程采购材料",
                {"technical_specification", "bid_response"},
            ),
            (
                "工程试运行材料",
                {"trial_run_report"},
            ),
            (
                "工程运营材料",
                {"operation_report"},
            ),
        )

        for label, expected_subtypes in cases:
            with self.subTest(label=label):
                request = deepcopy(self.fixture["cases"][1]["request"])
                request["task"]["instruction"] = (
                    "审阅这份{}，具体子类型尚未确认。".format(label)
                )
                request["material_view"]["title"] = label
                request["material_view"]["segments"][0]["text"] = (
                    "材料未提供可确定具体子类型的附加信息。"
                )

                decision = self.run_decision(request)["decision"]

                self.assertEqual(
                    "unknown", decision["material_subtype"]["value"]
                )
                candidates = decision["material_subtype"]["candidates"]
                self.assertEqual(
                    expected_subtypes,
                    {item["value"] for item in candidates},
                )
                self.assertTrue(
                    all(item["basis"].strip() for item in candidates)
                )
                self.assertIn(
                    "material_subtype", decision["pending_confirmations"]
                )
                self.assertEqual(
                    "recognition_coverage", decision["support_level"]
                )
                self.assertEqual(
                    "conservative_audit", decision["processing_mode"]
                )
                self.assertEqual(
                    [
                        "common.protected_spans",
                        "common.evidence_policy",
                        "common.statement_force_policy",
                        "common.quality_gate_h1_h6",
                    ],
                    decision["load_contracts"],
                )

    def test_generic_implementation_plan_keeps_domain_candidates(self):
        request = deepcopy(self.fixture["cases"][1]["request"])
        request["task"]["instruction"] = (
            "审阅这份实施方案，业务域和具体类型尚未确认。"
        )
        request["material_view"]["title"] = "实施方案"
        request["material_view"]["segments"][0]["text"] = (
            "本材料未提供可确定所属业务域的附加信息。"
        )

        decision = self.run_decision(request)["decision"]

        self.assertEqual(
            {"engineering_construction", "research_project"},
            {
                item["value"]
                for item in decision["business_domain"]["candidates"]
            },
        )
        self.assertEqual(
            {"implementation", "research_implementation"},
            {
                item["value"]
                for item in decision["lifecycle_position"]["candidates"]
            },
        )
        self.assertEqual(
            {
                "engineering_implementation_plan",
                "research_implementation_plan",
            },
            {
                item["value"]
                for item in decision["material_subtype"]["candidates"]
            },
        )
        self.assertEqual("recognition_coverage", decision["support_level"])
        self.assertEqual("conservative_audit", decision["processing_mode"])

    def test_ambiguous_research_stage_materials_keep_research_candidates(self):
        cases = (
            (
                "科研课题申报材料",
                {"application"},
                {"feasibility_study"},
                {
                    "research_application",
                    "research_feasibility_assessment",
                },
            ),
            (
                "科研课题任务约定材料",
                {"task_agreement"},
                {"technical_spec"},
                {"research_task_agreement"},
            ),
            (
                "科研课题研究实施材料",
                {"research_implementation"},
                {"architecture_design"},
                {"research_implementation_plan"},
            ),
            (
                "科研课题中期材料",
                {"midterm_review"},
                {"presentation", "review_acceptance"},
                {"research_interim_report", "research_interim_inspection"},
            ),
            (
                "科研课题验收报告",
                {"final_acceptance"},
                {"review_acceptance"},
                {"research_final_acceptance"},
            ),
        )

        for title, lifecycles, scenes, subtypes in cases:
            with self.subTest(title=title):
                request = deepcopy(self.fixture["cases"][1]["request"])
                request["task"]["instruction"] = (
                    "审阅这份{}，具体材料类型尚未确认。".format(title)
                )
                request["material_view"]["title"] = title
                request["material_view"]["segments"][0]["text"] = (
                    "本材料未提供可确定具体子类型的附加信息。"
                )

                decision = self.run_decision(request)["decision"]

                self.assertEqual("unknown", decision["business_domain"]["value"])
                self.assertEqual(
                    {"research_project"},
                    {
                        item["value"]
                        for item in decision["business_domain"]["candidates"]
                    },
                )
                self.assertEqual(
                    lifecycles,
                    {
                        item["value"]
                        for item in decision["lifecycle_position"]["candidates"]
                    },
                )
                self.assertEqual(
                    scenes,
                    {
                        item["value"]
                        for item in decision["document_scene"]["candidates"]
                    },
                )
                self.assertEqual(
                    subtypes,
                    {
                        item["value"]
                        for item in decision["material_subtype"]["candidates"]
                    },
                )
                self.assertEqual(
                    "recognition_coverage", decision["support_level"]
                )
                self.assertEqual(
                    "conservative_audit", decision["processing_mode"]
                )

    def test_conflicting_research_context_and_engineering_plan_stays_unclear(self):
        request = deepcopy(self.fixture["cases"][1]["request"])
        request["task"]["instruction"] = (
            "用户确认该材料属于科研课题，请审阅这份工程实施方案。"
        )
        request["material_view"]["title"] = "工程实施方案"
        request["material_view"]["segments"][0]["text"] = (
            "本材料未提供能够消解业务域冲突的附加信息。"
        )

        decision = self.run_decision(request)["decision"]

        self.assertEqual("unknown", decision["business_domain"]["value"])
        self.assertEqual(
            {"engineering_construction", "research_project"},
            {
                item["value"]
                for item in decision["business_domain"]["candidates"]
            },
        )
        self.assertEqual(
            {
                "engineering_implementation_plan",
                "research_implementation_plan",
            },
            {
                item["value"]
                for item in decision["material_subtype"]["candidates"]
            },
        )
        self.assertEqual("recognition_coverage", decision["support_level"])
        self.assertEqual("conservative_audit", decision["processing_mode"])

    def test_research_reference_does_not_override_governance_identity(self):
        for connector in (
            "依据",
            "引用",
            "参照",
            "参考",
            "根据",
            "按照",
            "基于",
            "见",
        ):
            with self.subTest(connector=connector):
                request = deepcopy(self.fixture["cases"][1]["request"])
                request["task"]["instruction"] = (
                    "审阅这份网络安全管理制度，只标出问题。"
                )
                request["material_view"]["title"] = "网络安全管理制度"
                request["material_view"]["segments"][0]["text"] = (
                    "本制度{}某科研课题任务书中的成果管理条款编制。".format(
                        connector
                    )
                )

                decision = self.run_decision(request)["decision"]

                self.assertEqual(
                    "governance_operation",
                    decision["business_domain"]["value"],
                )
                self.assertNotEqual(
                    "research_task_agreement",
                    decision["material_subtype"]["value"],
                )
                self.assertEqual(
                    "management_policy",
                    decision["material_subtype"]["value"],
                )
                self.assertEqual("basic_support", decision["support_level"])
                self.assertEqual("quick_path", decision["processing_mode"])

    def test_governance_material_reference_does_not_become_main_identity(self):
        for connector in (
            "依据",
            "引用",
            "参照",
            "参考",
            "根据",
            "按照",
            "基于",
            "见",
        ):
            with self.subTest(connector=connector):
                request = deepcopy(self.fixture["cases"][1]["request"])
                request["task"]["instruction"] = (
                    "审阅这份风险评估报告，只标出问题。"
                )
                request["material_view"]["title"] = "风险评估报告"
                request["material_view"]["segments"][0]["text"] = (
                    "本报告{}某网络安全管理制度开展评估。".format(
                        connector
                    )
                )

                decision = self.run_decision(request)["decision"]

                self.assertEqual(
                    "unknown", decision["business_domain"]["value"]
                )
                self.assertNotEqual(
                    "management_policy",
                    decision["material_subtype"]["value"],
                )
                self.assertEqual(
                    "recognition_coverage", decision["support_level"]
                )
                self.assertEqual(
                    "conservative_audit", decision["processing_mode"]
                )

    def test_long_governance_reference_does_not_become_main_identity(self):
        request = deepcopy(self.fixture["cases"][1]["request"])
        request["task"]["instruction"] = (
            "审阅这份风险评估报告，只标出问题。"
        )
        request["material_view"]["title"] = "风险评估报告"
        request["material_view"]["segments"][0]["text"] = (
            "本报告依据修订后的某集团总部及全部二级三级所属单位网络安全与"
            "数据安全统一运营管理制度开展评估。"
        )

        decision = self.run_decision(request)["decision"]

        self.assertEqual("unknown", decision["business_domain"]["value"])
        self.assertEqual("unknown", decision["material_subtype"]["value"])
        self.assertEqual("conservative_audit", decision["processing_mode"])

    def test_connector_before_task_target_does_not_hide_governance_identity(self):
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["task"]["instruction"] = (
            "请根据要求核查这份网络安全管理制度，只标出问题。"
        )
        request["material_view"]["title"] = "制度文件"
        request["material_view"]["segments"][0]["text"] = (
            "本合成片段只提供材料识别所需的最小信息。"
        )

        decision = self.run_decision(request)["decision"]

        self.assertEqual(
            "governance_operation", decision["business_domain"]["value"]
        )
        self.assertEqual(
            "management_policy", decision["material_subtype"]["value"]
        )
        self.assertEqual("quick_path", decision["processing_mode"])

    def test_engineering_plan_title_wins_over_research_plan_reference(self):
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["task"]["instruction"] = (
            "审阅这份工程实施方案，只标出问题。"
        )
        request["material_view"]["title"] = "某工程实施方案"
        request["material_view"]["segments"][0]["text"] = (
            "本工程实施方案依据某科研课题研究实施方案中的试验成果编制。"
        )

        decision = self.run_decision(request)["decision"]

        self.assertEqual(
            "engineering_construction",
            decision["business_domain"]["value"],
        )
        self.assertEqual(
            "implementation", decision["lifecycle_position"]["value"]
        )
        self.assertEqual(
            "engineering_implementation_plan",
            decision["material_subtype"]["value"],
        )

    def test_explicit_title_identity_wins_over_body_material_references(self):
        cases = (
            (
                "FOUNDATION-02-PRELIMINARY-DESIGN-NEAR-MISS",
                "本初步设计依据工程可研报告确定的建设范围编制。",
                "preliminary_design",
            ),
            (
                "FOUNDATION-02-BID-RESPONSE",
                "本文件逐条响应招标技术要求，并说明证明材料位置。",
                "bid_response",
            ),
            (
                "FOUNDATION-02-PRELIMINARY-DESIGN-NEAR-MISS",
                "本设计采用某科研课题形成的技术成果。",
                "preliminary_design",
            ),
            (
                "FOUNDATION-02-PRELIMINARY-DESIGN-NEAR-MISS",
                "本设计引用了某科研课题形成的技术成果。",
                "preliminary_design",
            ),
            (
                "FOUNDATION-02-PRELIMINARY-DESIGN-NEAR-MISS",
                "本设计采用来自某科研课题的成果。",
                "preliminary_design",
            ),
            (
                "FOUNDATION-02-PRELIMINARY-DESIGN-NEAR-MISS",
                "科研课题成果已在本工程中应用。",
                "preliminary_design",
            ),
            (
                "FOUNDATION-02-PRELIMINARY-DESIGN-NEAR-MISS",
                "科研课题成果用于本工程初步设计。",
                "preliminary_design",
            ),
        )

        for case_id, body_text, expected_subtype in cases:
            with self.subTest(case_id=case_id):
                case = next(
                    item
                    for item in self.fixture[
                        "engineering_construction_cases"
                    ]
                    if item["case_id"] == case_id
                )
                request = deepcopy(self.fixture["cases"][0]["request"])
                request["task"]["instruction"] = case["instruction"]
                request["material_view"]["title"] = case["title"]
                request["material_view"]["segments"][0]["text"] = body_text

                decision = self.run_decision(request)["decision"]

                self.assertEqual(
                    expected_subtype,
                    decision["material_subtype"]["value"],
                )
                self.assertEqual(
                    case["expected"]["document_scene"],
                    decision["document_scene"]["value"],
                )

    def test_task_negation_can_reject_an_explicit_title_identity(self):
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["task"]["instruction"] = (
            "审阅这份材料；用户确认这不是初步设计，具体文种待确认。"
        )

        decision = self.run_decision(request)["decision"]

        self.assertEqual("unknown", decision["material_subtype"]["value"])
        self.assertEqual(
            "conservative_audit", decision["processing_mode"]
        )
        self.assertIn("material_subtype", decision["pending_confirmations"])
        self.assertNotIn(
            "preliminary_design",
            {
                item["value"]
                for item in decision["material_subtype"]["candidates"]
            },
        )

    def test_task_replacement_can_correct_an_explicit_title_identity(self):
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["task"]["instruction"] = (
            "审阅这份材料；用户确认这不是初步设计，而是详细设计。"
        )

        decision = self.run_decision(request)["decision"]

        self.assertEqual(
            "detailed_design", decision["material_subtype"]["value"]
        )
        self.assertEqual(
            "architecture_design", decision["document_scene"]["value"]
        )
        self.assertEqual("explicit", decision["material_subtype"]["confidence"])

    def test_project_acceptance_does_not_imply_engineering_domain(self):
        cases = (
            (
                "某项目验收报告",
                {"engineering_construction"},
            ),
            (
                "某科研课题项目验收报告",
                {"research_project"},
            ),
        )

        for title, expected_domain_candidates in cases:
            with self.subTest(title=title):
                request = deepcopy(self.fixture["cases"][1]["request"])
                request["task"]["instruction"] = (
                    "审阅这份{}，只标出问题。".format(title)
                )
                request["material_view"]["title"] = title
                request["material_view"]["segments"][0]["text"] = (
                    "本材料未提供可改变业务域判断的其他信息。"
                )

                decision = self.run_decision(request)["decision"]

                self.assertEqual(
                    "unknown", decision["business_domain"]["value"]
                )
                self.assertEqual(
                    expected_domain_candidates,
                    {
                        item["value"]
                        for item in decision["business_domain"]["candidates"]
                    },
                )
                self.assertEqual(
                    "recognition_coverage", decision["support_level"]
                )
                self.assertEqual(
                    "conservative_audit", decision["processing_mode"]
                )

    def test_explicit_research_context_rejects_engineering_routes(self):
        cases = (
            ("某科研课题项目建议书", "unknown", None),
            ("某科研课题项目实施阶段汇报", "unknown", None),
            (
                "某科研课题研究实施方案",
                "research_project",
                "scene.architecture_design",
            ),
            (
                "某科研课题中期阶段汇报",
                "research_project",
                "scene.presentation",
            ),
        )

        for title, expected_domain, expected_contract in cases:
            with self.subTest(title=title):
                request = deepcopy(self.fixture["cases"][1]["request"])
                request["task"]["instruction"] = (
                    "审阅这份{}，只标出问题。".format(title)
                )
                request["material_view"]["title"] = title
                request["material_view"]["segments"][0]["text"] = (
                    "本材料未提供可改变业务域判断的其他信息。"
                )

                decision = self.run_decision(request)["decision"]

                self.assertEqual(
                    expected_domain,
                    decision["business_domain"]["value"],
                )
                self.assertNotIn(
                    "engineering_construction",
                    {
                        item["value"]
                        for item in decision[
                            "business_domain"
                        ]["candidates"]
                    },
                )
                if expected_domain == "unknown":
                    self.assertEqual(
                        [
                            "common.protected_spans",
                            "common.evidence_policy",
                            "common.statement_force_policy",
                            "common.quality_gate_h1_h6",
                        ],
                        decision["load_contracts"],
                    )
                else:
                    self.assertIn(
                        expected_contract,
                        decision["load_contracts"],
                    )

    def test_research_context_outside_title_overrides_engineering_title_route(self):
        cases = (
            (
                "审阅这份科研课题项目建议书，只标出问题。",
                "本材料未提供其他分类信息。",
            ),
            (
                "审阅这份项目建议书，只标出问题。",
                "本材料属于科研课题语境。",
            ),
        )

        for instruction, body in cases:
            with self.subTest(instruction=instruction, body=body):
                request = deepcopy(self.fixture["cases"][1]["request"])
                request["task"]["instruction"] = instruction
                request["material_view"]["title"] = "项目建议书"
                request["material_view"]["segments"][0]["text"] = body

                decision = self.run_decision(request)["decision"]

                self.assertEqual(
                    "unknown", decision["business_domain"]["value"]
                )
                self.assertNotIn(
                    "engineering_construction",
                    {
                        item["value"]
                        for item in decision[
                            "business_domain"
                        ]["candidates"]
                    },
                )
                self.assertEqual(
                    "recognition_coverage", decision["support_level"]
                )

    def test_negated_research_context_allows_explicit_engineering_replacement(self):
        request = deepcopy(self.fixture["cases"][1]["request"])
        request["task"]["instruction"] = (
            "用户确认这不是科研课题材料，而是工程初步设计说明书。"
        )
        request["material_view"]["title"] = "材料说明"
        request["material_view"]["segments"][0]["text"] = (
            "本材料未提供其他分类信息。"
        )

        decision = self.run_decision(request)["decision"]

        self.assertEqual(
            "engineering_construction",
            decision["business_domain"]["value"],
        )
        self.assertEqual(
            "preliminary_design", decision["material_subtype"]["value"]
        )
        self.assertEqual("explicit", decision["material_subtype"]["confidence"])

    def test_generic_negation_excludes_rejected_material_candidates(self):
        cases = (
            (
                "实施方案",
                "用户确认这不是实施方案，具体材料子类型待确认。",
                "engineering_implementation_plan",
            ),
            (
                "某项目验收报告",
                "用户确认这不是项目验收报告，具体文种待确认。",
                "acceptance_report",
            ),
        )

        for title, instruction, rejected_subtype in cases:
            with self.subTest(title=title):
                request = deepcopy(self.fixture["cases"][1]["request"])
                request["task"]["instruction"] = instruction
                request["material_view"]["title"] = title
                request["material_view"]["segments"][0]["text"] = (
                    "本材料未提供其他分类信息。"
                )

                decision = self.run_decision(request)["decision"]

                self.assertNotIn(
                    rejected_subtype,
                    {
                        item["value"]
                        for item in decision[
                            "material_subtype"
                        ]["candidates"]
                    },
                )
                self.assertEqual(
                    "conservative_audit", decision["processing_mode"]
                )

    def test_recognized_engineering_document_creation_uses_two_stage_only(self):
        case = next(
            item
            for item in self.fixture["engineering_construction_cases"]
            if item["case_id"] == "FOUNDATION-02-FEASIBILITY-STUDY"
        )
        request = deepcopy(self.fixture["cases"][0]["request"])
        request["task"] = {
            "instruction": "新建一份完整的工程可研报告。",
            "mode": "create",
            "scope": "document",
        }
        request["material_view"]["title"] = case["title"]
        request["material_view"]["segments"][0]["text"] = (
            "本合成片段只提供材料识别所需的最小信息。"
        )

        decision = self.run_decision(request)["decision"]

        self.assertEqual(
            "feasibility_study", decision["material_subtype"]["value"]
        )
        self.assertEqual("recognition_coverage", decision["support_level"])
        self.assertEqual("two_stage", decision["processing_mode"])
        self.assertIn("writing_preparation_sheet", decision)
        self.assertIn(
            "common.writing_preparation", decision["load_contracts"]
        )
        self.assertNotIn(
            "scene.feasibility_study", decision["load_contracts"]
        )

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
