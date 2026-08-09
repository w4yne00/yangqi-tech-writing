from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "evals/foundation-synthetic-benchmark.json"
PERCEPTION_FIXTURE = ROOT / "tests/fixtures/perception-decision-cases.json"
CONTEXT_FIXTURE = ROOT / "tests/fixtures/project-context-cases.json"
PERCEPTION_SCRIPT = ROOT / "scripts/perception_decision.py"
CONTEXT_SCRIPT = ROOT / "scripts/project_context.py"


class FoundationSyntheticBenchmarkTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.benchmark = json.loads(BENCHMARK.read_text(encoding="utf-8"))
        cls.perception_fixture = json.loads(
            PERCEPTION_FIXTURE.read_text(encoding="utf-8")
        )
        cls.context_fixture = json.loads(
            CONTEXT_FIXTURE.read_text(encoding="utf-8")
        )

    def run_json_script(self, script, request, extra_args=None):
        command = [sys.executable, str(script), "-"]
        if extra_args:
            command.extend(extra_args)
        return subprocess.run(
            command,
            input=json.dumps(request, ensure_ascii=False),
            capture_output=True,
            check=False,
            text=True,
        )

    def run_perception(self, request):
        completed = self.run_json_script(PERCEPTION_SCRIPT, request)
        self.assertEqual(0, completed.returncode, completed.stderr)
        return json.loads(completed.stdout)["decision"]

    def base_perception_request(self):
        return deepcopy(self.perception_fixture["cases"][0]["request"])

    def fixture_case(self, collection, case_id):
        return next(
            item
            for item in self.perception_fixture[collection]
            if item["case_id"] == case_id
        )

    def request_for_case(self, item):
        request = self.base_perception_request()
        profile = item["input_profile"]
        source_case_id = item.get("source_case_id")

        if profile == "identified_material":
            source = self.fixture_case(
                item["source_collection"], source_case_id
            )
            request["task"]["instruction"] = source["instruction"]
            request["material_view"]["title"] = source["title"]
            request["material_view"]["segments"][0]["text"] = (
                "本合成片段只提供统一基准识别所需的最小信息。"
            )
        elif profile == "statement_force":
            source = self.fixture_case(
                "statement_force_cases", source_case_id
            )
            request["claims"] = deepcopy(source["claims"])
        elif profile == "material_set":
            source = self.fixture_case("material_set_cases", source_case_id)
            request["material_set"] = deepcopy(source["material_set"])
        elif profile == "quick_path":
            pass
        elif profile == "two_stage":
            request["task"] = {
                "instruction": "新建一份完整的初步设计说明书。",
                "mode": "create",
                "scope": "document",
            }
        elif profile == "formal_template":
            request["formal_template"] = {
                "template_id": "F12-TPL-001",
                "template_name": "合成正式模板",
                "source_ref": "维护者提供的合成模板约束",
                "controls": {
                    "chapters": ["1 设计依据", "2 总体设计"],
                    "numbering": "preserve",
                    "tables": ["接口关系表"],
                    "required_items": ["编制人", "审核人"],
                },
            }
        elif profile == "extraction_gap":
            request["claims"] = [
                {
                    "claim_id": "F12-HIGH-001",
                    "text": "系统已满足全部接口验收要求。",
                    "risk": "high",
                    "evidence_status": "SUPPORTED",
                    "statement_force": "acceptance_conclusion",
                    "source_ref": "F12-TABLE-001",
                }
            ]
            request["material_view"]["extraction_gaps"] = [
                {
                    "gap_id": "F12-GAP-001",
                    "gap_type": "table_relationship_lost",
                    "locator": {"table": "表12"},
                    "description": "接口关系表的行列关系未能恢复。",
                    "affected_claim_ids": ["F12-HIGH-001"],
                }
            ]
        else:
            self.fail("未知 input_profile: {}".format(profile))
        return request

    def integration_observations(self, decision):
        claims = decision.get("claim_decisions") or [{}]
        material_review = decision.get("material_set_review", {})
        structure = decision.get("structure_adaptation", {})
        extraction = decision.get("extraction_gap_review", {})
        return {
            "processing_mode": decision.get("processing_mode"),
            "allowed_statement_force": claims[0].get(
                "allowed_statement_force"
            ),
            "action": claims[0].get("action"),
            "relationship_types": [
                relation["relation_type"]
                for relation in material_review.get("relationships", [])
            ],
            "conflict_dimensions": [
                conflict["dimension"]
                for conflict in material_review.get("conflicts", [])
            ],
            "review_status": material_review.get("review_status"),
            "mode": structure.get("mode"),
            "structure_authority": structure.get("structure_authority"),
            "material_contract_role": structure.get(
                "material_contract_role"
            ),
            "status": extraction.get("status"),
            "blocked_claim_ids": extraction.get("blocked_claim_ids"),
        }

    def test_metadata_limits_the_public_evidence_claim(self):
        data = self.benchmark

        self.assertEqual("1.0", data["schema_version"])
        self.assertEqual(
            "deterministic-synthetic-fixture", data["evidence_type"]
        )
        self.assertFalse(data["model_execution"])
        self.assertFalse(data["real_engineering_evidence"])
        self.assertEqual(
            ["recognition_coverage", "basic_support"],
            data["permitted_support_claims"],
        )
        self.assertEqual(
            {
                "deep_support",
                "joint_review_support",
                "forward_validation",
                "statistical_stability",
            },
            set(data["prohibited_claims"]),
        )
        self.assertIn("确定性合成", data["statement"])
        self.assertIn("非真实工程证据", data["statement"])
        self.assertIn("不代表模型运行表现", data["statement"])
        self.assertFalse(
            self.perception_fixture["real_engineering_evidence"]
        )
        self.assertFalse(self.context_fixture["real_engineering_evidence"])
        case_groups = (
            data["identity_cases"],
            data["integration_cases"],
            data["project_context_cases"],
            data["data_boundary_cases"],
        )
        case_ids = [
            item["case_id"] for group in case_groups for item in group
        ]
        self.assertEqual(data["case_count"], len(case_ids))
        self.assertEqual(len(case_ids), len(set(case_ids)))

    def test_identity_matrix_covers_domains_scenes_near_misses_and_composites(self):
        observed_domains = set()
        observed_scenes = set()
        observed_kinds = set()

        for item in self.benchmark["identity_cases"]:
            with self.subTest(case_id=item["case_id"]):
                decision = self.run_perception(self.request_for_case(item))
                expected = item["expected"]
                observed_kinds.add(item["coverage_kind"])

                for dimension in (
                    "business_domain",
                    "lifecycle_position",
                    "document_scene",
                    "material_subtype",
                ):
                    if dimension in expected:
                        self.assertEqual(
                            expected[dimension], decision[dimension]["value"]
                        )
                        self.assertEqual(
                            "explicit", decision[dimension]["confidence"]
                        )
                observed_domains.add(decision["business_domain"]["value"])
                observed_scenes.add(decision["document_scene"]["value"])
                self.assertIn(
                    decision["support_level"],
                    self.benchmark["permitted_support_claims"],
                )

                if item["coverage_kind"] == "composite_material":
                    self.assertEqual(
                        expected["primary_scene"],
                        decision["composite_routing"]["primary_scene"]["value"],
                    )
                    self.assertEqual(
                        expected["local_scene"],
                        decision["composite_routing"]["local_scene"]["value"],
                    )

        self.assertEqual(
            {
                "engineering_construction",
                "research_project",
                "governance_operation",
            },
            observed_domains,
        )
        self.assertEqual(
            {
                "feasibility_study",
                "architecture_design",
                "technical_spec",
                "bid_response",
                "security_policy",
                "presentation",
                "review_acceptance",
            },
            observed_scenes,
        )
        self.assertEqual(
            {"scene_positive", "lifecycle_near_miss", "composite_material"},
            observed_kinds,
        )

    def test_processing_force_material_template_and_gap_matrix(self):
        observed_profiles = set()

        for item in self.benchmark["integration_cases"]:
            with self.subTest(case_id=item["case_id"]):
                decision = self.run_perception(self.request_for_case(item))
                expected = item["expected"]
                profile = item["input_profile"]
                observed_profiles.add(profile)
                observations = self.integration_observations(decision)
                for field, expected_value in expected.items():
                    if field == "blocker":
                        self.assertIn(expected_value, decision["blockers"])
                    else:
                        self.assertEqual(
                            expected_value,
                            observations[field],
                            field,
                        )

                serialized = json.dumps(decision, ensure_ascii=False)
                for claim in self.benchmark["prohibited_claims"]:
                    self.assertNotIn(claim, serialized)

        self.assertEqual(
            {
                "statement_force",
                "quick_path",
                "two_stage",
                "material_set",
                "formal_template",
                "extraction_gap",
            },
            observed_profiles,
        )

    def test_project_context_update_and_isolation_use_the_public_context_seam(self):
        profiles = {
            item["input_profile"]: item
            for item in self.benchmark["project_context_cases"]
        }
        self.assertEqual(
            {"confirmed_then_upstream_change", "cross_project_isolation"},
            set(profiles),
        )
        update_expected = profiles["confirmed_then_upstream_change"][
            "expected"
        ]
        isolation_expected = profiles["cross_project_isolation"]["expected"]

        with tempfile.TemporaryDirectory() as directory:
            context_path = Path(directory) / "project-context.json"
            initial = self.run_json_script(
                CONTEXT_SCRIPT,
                deepcopy(self.context_fixture["confirmed_update"]),
                ["--context", str(context_path)],
            )
            self.assertEqual(0, initial.returncode, initial.stderr)
            self.assertEqual(
                update_expected["initial_status"],
                json.loads(initial.stdout)["persistence"]["status"],
            )

            changed = self.run_json_script(
                CONTEXT_SCRIPT,
                deepcopy(self.context_fixture["upstream_change"]),
                ["--context", str(context_path)],
            )
            self.assertEqual(0, changed.returncode, changed.stderr)
            changed_result = json.loads(changed.stdout)["persistence"]
            self.assertEqual(
                update_expected["changed_status"], changed_result["status"]
            )
            self.assertEqual(
                ["CONCLUSION-001"],
                changed_result["invalidated"]["conclusion_ids"],
            )
            context = json.loads(context_path.read_text(encoding="utf-8"))
            self.assertEqual(
                update_expected["dependent_review_status"],
                context["conclusions"][0]["review_status"],
            )

            original = context_path.read_bytes()
            cross_project = deepcopy(self.context_fixture["upstream_change"])
            cross_project["project_id"] = "SYNTHETIC-PROJECT-B"
            cross_project["expected_revision"] = 2
            isolated = self.run_json_script(
                CONTEXT_SCRIPT,
                cross_project,
                ["--context", str(context_path)],
            )
            self.assertEqual(isolation_expected["exit_code"], isolated.returncode)
            self.assertEqual(
                isolation_expected["error"],
                json.loads(isolated.stderr)["error"],
            )
            if not isolation_expected["mutation"]:
                self.assertEqual(original, context_path.read_bytes())

    def test_prohibited_persistence_input_is_rejected_without_echo_or_write(self):
        profile = next(
            item
            for item in self.benchmark["data_boundary_cases"]
            if item["input_profile"] == "prohibited_persistence_placeholder"
        )
        request = deepcopy(self.context_fixture["confirmed_update"])
        sensitive_field = "api_" + "token"
        sensitive_value = "ghp_" + "9" * 32
        request["update"]["facts"][0][sensitive_field] = sensitive_value

        with tempfile.TemporaryDirectory() as directory:
            context_path = Path(directory) / "project-context.json"
            completed = self.run_json_script(
                CONTEXT_SCRIPT,
                request,
                ["--context", str(context_path)],
            )

            self.assertEqual(profile["expected_exit_code"], completed.returncode)
            self.assertEqual(
                profile["expected_error"],
                json.loads(completed.stderr)["error"],
            )
            self.assertNotIn(sensitive_value, completed.stderr)
            self.assertNotIn(sensitive_value, completed.stdout)
            self.assertFalse(context_path.exists())

    def test_stable_evals_triggers_and_audit_script_contracts_remain_intact(self):
        contracts = self.benchmark["regression_contracts"]
        evals = json.loads(
            (ROOT / "evals/evals.json").read_text(encoding="utf-8")
        )
        triggers = json.loads(
            (ROOT / "evals/trigger-evals.json").read_text(encoding="utf-8")
        )

        self.assertEqual(contracts["behavior_eval_count"], len(evals["evals"]))
        self.assertEqual(contracts["trigger_eval_count"], len(triggers))
        self.assertEqual(
            contracts["stable_version"],
            (ROOT / "VERSION").read_text(encoding="utf-8").strip(),
        )

        regression = subprocess.run(
            [
                sys.executable,
                "-m",
                "unittest",
                *contracts["stable_contract_test_modules"],
            ],
            cwd=str(ROOT),
            capture_output=True,
            check=False,
            text=True,
        )
        self.assertEqual(0, regression.returncode, regression.stderr)

        for audit in contracts["audit_scripts"]:
            with self.subTest(script=audit["script"]):
                completed = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / audit["script"]),
                        *[str(ROOT / path) for path in audit["arguments"]],
                    ],
                    capture_output=True,
                    check=False,
                    text=True,
                )
                self.assertEqual(
                    audit["expected_exit_code"],
                    completed.returncode,
                    completed.stderr,
                )
                json.loads(completed.stdout)

    def test_public_capability_docs_keep_the_benchmark_claim_honest(self):
        reference = (
            ROOT / "references/foundation-synthetic-benchmark.md"
        ).read_text(encoding="utf-8")
        for phrase in (
            "确定性合成证据基准",
            "非真实工程证据",
            "识别覆盖",
            "基础支持",
            "不构成深度支持",
            "不构成联审支持",
            "不构成前向验证",
            "不证明统计稳定性",
        ):
            self.assertIn(phrase, reference)

        for name in (
            "README.md",
            "TESTING.md",
            "CHANGELOG.md",
            "docs/codex-handoff.md",
        ):
            text = (ROOT / name).read_text(encoding="utf-8")
            self.assertIn("Foundation 12", text, name)
            self.assertIn("非真实工程证据", text, name)


if __name__ == "__main__":
    unittest.main()
