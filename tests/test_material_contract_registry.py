from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/material_contract_registry.py"
FIXTURE = ROOT / "tests/fixtures/material-contract-cases.json"
TEMPLATE = ROOT / "templates/material-contract-evidence-bundle.json"


class MaterialContractRegistryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def base_bundle(self):
        return deepcopy(self.fixture["simulated_basic_support_input"])

    def run_bundle(self, bundle):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "-"],
            input=json.dumps(bundle, ensure_ascii=False),
            capture_output=True,
            check=False,
            text=True,
        )

    def simulate_real_case_metadata(self, bundle):
        sample = bundle["samples"][0]
        sample["source"]["source_type"] = "real_case"
        sample["evidence_type"] = "deidentified-real-case"
        sample["redaction_status"] = "redacted"
        sample["review_status"] = "approved"
        sample["case_type"] = "positive"
        sample["authorization"] = {
            "status": "authorized",
            "scope": [
                "private_review",
                "generic_rule",
                "public_eval",
                "capability_evidence",
            ],
        }
        sample["intended_uses"] = [
            "generic_rule",
            "capability_evidence",
        ]
        return sample

    def test_valid_basic_bundle_passes_without_capability_evidence(self):
        completed = self.run_bundle(self.base_bundle())

        self.assertEqual(0, completed.returncode, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual("valid", result["validation"]["status"])
        self.assertEqual("basic_support", result["contract"]["support_level"])
        self.assertEqual(
            {}, result["evidence_summary"]["eligible_case_counts"]
        )
        self.assertEqual(
            ["SIM-SYNTHETIC-001"],
            result["evidence_summary"]["excluded_sample_ids"],
        )
        self.assertEqual(
            "deterministic-synthetic-fixture",
            self.fixture["evidence_type"],
        )
        self.assertFalse(self.fixture["model_execution"])
        self.assertIn("不代表深度支持", self.fixture["statement"])

    def test_distributed_template_contains_complete_contract_and_sample_entry(self):
        template = json.loads(TEMPLATE.read_text(encoding="utf-8"))

        completed = self.run_bundle(template)

        self.assertEqual(0, completed.returncode, completed.stderr)
        contract = template["contract"]
        for field in [
            "applicable_identity",
            "required_inputs",
            "content_responsibilities",
            "reasonable_depth",
            "statement_force",
            "traceability",
            "common_failures",
            "missing_information_handling",
            "validation_case_ids",
            "support_level",
        ]:
            self.assertIn(field, contract)
        sample = template["samples"][0]
        for field in [
            "source",
            "authorization",
            "redaction_status",
            "material_version",
            "review_status",
            "case_type",
            "data_classification",
            "intended_uses",
            "evidence_type",
            "model_execution",
        ]:
            self.assertIn(field, sample)

    def test_missing_sample_metadata_is_rejected(self):
        bundle = self.base_bundle()
        del bundle["samples"][0]["authorization"]

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("missing_sample_metadata", error["error"])
        self.assertIn("authorization", error["message"])

    def test_missing_contract_metadata_returns_a_structured_error(self):
        bundle = self.base_bundle()
        del bundle["contract"]["required_inputs"][0]["description"]

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("missing_contract_metadata", error["error"])
        self.assertIn("description", error["message"])

    def test_statement_force_transition_rejects_unknown_endpoints(self):
        bundle = self.base_bundle()
        bundle["contract"]["statement_force"]["prohibited_transitions"][0][
            "from"
        ] = "invented_force"

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("invalid_bundle", error["error"])
        self.assertIn("invented_force", error["message"])

    def test_unredacted_real_sample_is_blocked(self):
        bundle = self.base_bundle()
        sample = self.simulate_real_case_metadata(bundle)
        sample["redaction_status"] = "pending"

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("unredacted_sample", error["error"])
        self.assertIn("SIM-SYNTHETIC-001", error["message"])

    def test_project_restricted_sample_cannot_enter_reusable_uses(self):
        bundle = self.base_bundle()
        sample = self.simulate_real_case_metadata(bundle)
        sample["data_classification"] = "project_restricted"

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("project_restricted_scope_violation", error["error"])
        self.assertNotIn(
            sample["source"]["source_id"],
            error["message"],
        )

    def test_restricted_authorization_cannot_enter_reusable_uses(self):
        bundle = self.base_bundle()
        sample = self.simulate_real_case_metadata(bundle)
        sample["authorization"]["status"] = "restricted"

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("authorization_scope_violation", error["error"])

    def test_intended_uses_cannot_exceed_authorization_scope(self):
        bundle = self.base_bundle()
        sample = self.simulate_real_case_metadata(bundle)
        sample["authorization"]["scope"] = ["private_review"]

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("authorization_scope_violation", error["error"])
        self.assertIn("capability_evidence", error["message"])

    def test_unapproved_sample_cannot_enter_reusable_uses(self):
        bundle = self.base_bundle()
        sample = self.simulate_real_case_metadata(bundle)
        sample["review_status"] = "rejected"

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("review_status_violation", error["error"])

    def test_prohibited_persistence_information_is_rejected_without_echo(self):
        bundle = self.base_bundle()
        secret_value = "Bearer ABCDEFGHIJKLMNOPQRSTUV"
        bundle["samples"][0]["source"]["locator"] = secret_value

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual(
            "persistence_rejected_sensitive_data", error["error"]
        )
        self.assertIn("禁止持久化信息", error["message"])
        self.assertNotIn(secret_value, error["message"])

    def test_explicit_prohibited_persistence_classification_is_blocked(self):
        bundle = self.base_bundle()
        bundle["samples"][0]["data_classification"] = (
            "prohibited_persistence"
        )

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual(
            "persistence_rejected_sensitive_data", error["error"]
        )

    def test_project_restricted_sample_can_be_recorded_for_private_review(self):
        bundle = self.base_bundle()
        bundle["samples"][0]["data_classification"] = "project_restricted"

        completed = self.run_bundle(bundle)

        self.assertEqual(0, completed.returncode, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertIn(
            "SIM-SYNTHETIC-001",
            result["evidence_summary"]["excluded_sample_ids"],
        )

    def test_synthetic_sample_requires_explicit_evidence_metadata(self):
        bundle = self.base_bundle()
        bundle["samples"][0]["evidence_type"] = "unspecified"

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual(
            "invalid_synthetic_evidence_metadata", error["error"]
        )
        self.assertIn("deterministic-synthetic-fixture", error["message"])

    def test_valid_synthetic_sample_is_not_counted_as_real_evidence(self):
        completed = self.run_bundle(self.base_bundle())

        self.assertEqual(0, completed.returncode, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual(
            {}, result["evidence_summary"]["eligible_case_counts"]
        )

    def test_simulated_forward_metadata_requires_recorded_model_execution(self):
        bundle = self.base_bundle()
        sample = self.simulate_real_case_metadata(bundle)
        sample["case_type"] = "forward_validation"
        sample["model_execution"] = False

        without_execution = self.run_bundle(bundle)

        self.assertEqual(
            0, without_execution.returncode, without_execution.stderr
        )
        result = json.loads(without_execution.stdout)
        self.assertEqual(
            {}, result["evidence_summary"]["eligible_case_counts"]
        )

        sample["model_execution"] = True
        with_execution = self.run_bundle(bundle)

        self.assertEqual(0, with_execution.returncode, with_execution.stderr)
        result = json.loads(with_execution.stdout)
        self.assertEqual(
            {"forward_validation": 1},
            result["evidence_summary"]["eligible_case_counts"],
        )

    def test_synthetic_cases_cannot_unlock_deep_support(self):
        bundle = self.base_bundle()
        bundle["contract"]["support_level"] = "deep_support"

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("unsupported_capability_claim", error["error"])
        for case_type in [
            "formal_requirement",
            "positive",
            "failure",
            "lifecycle_boundary",
            "missing_information",
        ]:
            self.assertIn(case_type, error["message"])

    def test_joint_review_support_requires_joint_review_real_cases(self):
        bundle = self.base_bundle()
        bundle["contract"]["support_level"] = "joint_review_support"

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("unsupported_capability_claim", error["error"])
        for case_type in [
            "traceability_gap",
            "version_conflict",
            "statement_force_unclear",
            "explicit_supersession",
        ]:
            self.assertIn(case_type, error["message"])

    def test_real_case_cannot_be_mislabeled_as_a_formal_requirement(self):
        bundle = self.base_bundle()
        sample = self.simulate_real_case_metadata(bundle)
        sample["case_type"] = "formal_requirement"

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("invalid_evidence_metadata", error["error"])
        self.assertIn("formal_requirement", error["message"])


if __name__ == "__main__":
    unittest.main()
