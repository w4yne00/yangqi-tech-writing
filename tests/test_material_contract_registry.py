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

    def run_bundle(self, bundle):
        return subprocess.run(
            [sys.executable, str(SCRIPT), "-"],
            input=json.dumps(bundle, ensure_ascii=False),
            capture_output=True,
            check=False,
            text=True,
        )

    def test_valid_deep_support_bundle_passes_with_evidence_summary(self):
        completed = self.run_bundle(
            deepcopy(self.fixture["valid_deep_support_bundle"])
        )

        self.assertEqual(0, completed.returncode, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual("valid", result["validation"]["status"])
        self.assertEqual("deep_support", result["contract"]["support_level"])
        self.assertEqual(
            {
                "formal_requirement": 1,
                "positive": 1,
                "failure": 1,
                "lifecycle_boundary": 1,
                "missing_information": 1,
            },
            result["evidence_summary"]["eligible_case_counts"],
        )
        self.assertEqual([], result["evidence_summary"]["excluded_sample_ids"])

    def test_missing_sample_metadata_is_rejected(self):
        bundle = deepcopy(self.fixture["valid_deep_support_bundle"])
        del bundle["samples"][1]["authorization"]

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("missing_sample_metadata", error["error"])
        self.assertIn("authorization", error["message"])

    def test_unredacted_real_sample_is_blocked(self):
        bundle = deepcopy(self.fixture["valid_deep_support_bundle"])
        bundle["samples"][1]["redaction_status"] = "pending"

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("unredacted_sample", error["error"])
        self.assertIn("SIM-POS-001", error["message"])

    def test_project_restricted_sample_cannot_enter_generic_or_public_uses(self):
        bundle = deepcopy(self.fixture["valid_deep_support_bundle"])
        bundle["samples"][1]["data_classification"] = "project_restricted"

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("project_restricted_scope_violation", error["error"])
        self.assertIn("SIM-POS-001", error["message"])
        self.assertNotIn(
            bundle["samples"][1]["source"]["source_id"],
            error["message"],
        )

    def test_restricted_authorization_cannot_enter_reusable_uses(self):
        bundle = deepcopy(self.fixture["valid_deep_support_bundle"])
        bundle["contract"]["support_level"] = "basic_support"
        bundle["samples"][1]["authorization"]["status"] = "restricted"

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("authorization_scope_violation", error["error"])
        self.assertIn("SIM-POS-001", error["message"])

    def test_prohibited_persistence_information_is_rejected_without_echo(self):
        bundle = deepcopy(self.fixture["valid_deep_support_bundle"])
        secret_value = "Bearer ABCDEFGHIJKLMNOPQRSTUV"
        bundle["samples"][1]["source"]["locator"] = secret_value

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual(
            "persistence_rejected_sensitive_data", error["error"]
        )
        self.assertIn("禁止持久化信息", error["message"])
        self.assertNotIn(secret_value, error["message"])

    def test_synthetic_sample_requires_explicit_evidence_metadata(self):
        bundle = deepcopy(self.fixture["valid_deep_support_bundle"])
        bundle["contract"]["support_level"] = "basic_support"
        sample = bundle["samples"][1]
        sample["source"]["source_type"] = "synthetic_case"
        sample["evidence_type"] = "unspecified"

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual(
            "invalid_synthetic_evidence_metadata", error["error"]
        )
        self.assertIn("deterministic-synthetic-fixture", error["message"])

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

    def test_missing_contract_metadata_returns_a_structured_error(self):
        bundle = deepcopy(self.fixture["valid_deep_support_bundle"])
        del bundle["contract"]["required_inputs"][0]["description"]

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("missing_contract_metadata", error["error"])
        self.assertIn("description", error["message"])

    def test_explicit_prohibited_persistence_classification_is_blocked(self):
        bundle = deepcopy(self.fixture["valid_deep_support_bundle"])
        bundle["contract"]["support_level"] = "basic_support"
        bundle["samples"][1]["data_classification"] = (
            "prohibited_persistence"
        )
        bundle["samples"][1]["intended_uses"] = ["private_review"]

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual(
            "persistence_rejected_sensitive_data", error["error"]
        )
        self.assertIn("SIM-POS-001", error["message"])

    def test_project_restricted_sample_can_be_recorded_for_private_review(self):
        bundle = deepcopy(self.fixture["valid_deep_support_bundle"])
        bundle["contract"]["support_level"] = "basic_support"
        sample = bundle["samples"][1]
        sample["data_classification"] = "project_restricted"
        sample["intended_uses"] = ["private_review"]

        completed = self.run_bundle(bundle)

        self.assertEqual(0, completed.returncode, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertIn(
            "SIM-POS-001",
            result["evidence_summary"]["excluded_sample_ids"],
        )

    def test_valid_synthetic_sample_is_recorded_but_not_counted_as_real_evidence(self):
        bundle = deepcopy(self.fixture["valid_deep_support_bundle"])
        bundle["contract"]["support_level"] = "basic_support"
        sample = bundle["samples"][1]
        sample["source"]["source_type"] = "synthetic_case"
        sample["evidence_type"] = "deterministic-synthetic-fixture"
        sample["model_execution"] = False

        completed = self.run_bundle(bundle)

        self.assertEqual(0, completed.returncode, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertIn(
            "SIM-POS-001",
            result["evidence_summary"]["excluded_sample_ids"],
        )
        self.assertNotIn(
            "positive",
            result["evidence_summary"]["eligible_case_counts"],
        )

    def test_synthetic_cases_cannot_unlock_deep_support(self):
        bundle = deepcopy(self.fixture["valid_deep_support_bundle"])
        sample = bundle["samples"][1]
        sample["source"]["source_type"] = "synthetic_case"
        sample["evidence_type"] = "deterministic-synthetic-fixture"

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("unsupported_capability_claim", error["error"])
        self.assertIn("positive", error["message"])

    def test_joint_review_support_requires_joint_review_real_cases(self):
        bundle = deepcopy(self.fixture["valid_deep_support_bundle"])
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
        bundle = deepcopy(self.fixture["valid_deep_support_bundle"])
        sample = bundle["samples"][0]
        sample["source"]["source_type"] = "real_case"
        sample["redaction_status"] = "redacted"
        sample["evidence_type"] = "deidentified-real-case"

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("invalid_evidence_metadata", error["error"])
        self.assertIn("formal_requirement", error["message"])

    def test_forward_validation_requires_recorded_model_execution(self):
        bundle = deepcopy(self.fixture["valid_deep_support_bundle"])
        bundle["contract"]["support_level"] = "forward_validation"
        for case_type in [
            "traceability_gap",
            "version_conflict",
            "statement_force_unclear",
            "explicit_supersession",
            "forward_validation",
        ]:
            sample = deepcopy(bundle["samples"][1])
            sample_id = "SIM-{}".format(case_type.upper())
            sample["sample_id"] = sample_id
            sample["source"]["source_id"] = "{}-SOURCE".format(sample_id)
            sample["case_type"] = case_type
            sample["model_execution"] = False
            bundle["samples"].append(sample)
            bundle["contract"]["validation_case_ids"].append(sample_id)

        completed = self.run_bundle(bundle)

        self.assertEqual(1, completed.returncode)
        error = json.loads(completed.stderr)
        self.assertEqual("unsupported_capability_claim", error["error"])
        self.assertIn("forward_validation", error["message"])


if __name__ == "__main__":
    unittest.main()
