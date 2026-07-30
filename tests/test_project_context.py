from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/project_context.py"
FIXTURE = ROOT / "tests/fixtures/project-context-cases.json"


class ProjectContextTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def run_request(self, request, context_path=None):
        command = [sys.executable, str(SCRIPT), "-"]
        if context_path is not None:
            command.extend(["--context", str(context_path)])
        return subprocess.run(
            command,
            input=json.dumps(request, ensure_ascii=False),
            capture_output=True,
            check=False,
            text=True,
        )

    def load_context(self, context_path):
        return json.loads(context_path.read_text(encoding="utf-8"))

    def test_context_is_optional_and_no_path_means_no_persistence(self):
        request = deepcopy(self.fixture["confirmed_update"])

        completed = self.run_request(request)

        self.assertEqual(0, completed.returncode, completed.stderr)
        result = json.loads(completed.stdout)
        self.assertEqual("not_requested", result["persistence"]["status"])
        self.assertEqual(
            "single_task_without_persistence",
            result["persistence"]["reason"],
        )

    def test_confirmed_user_update_creates_local_isolated_package(self):
        with tempfile.TemporaryDirectory() as directory:
            context_path = Path(directory) / "project-context.json"

            completed = self.run_request(
                deepcopy(self.fixture["confirmed_update"]),
                context_path,
            )

            self.assertEqual(0, completed.returncode, completed.stderr)
            result = json.loads(completed.stdout)
            self.assertEqual("saved", result["persistence"]["status"])
            self.assertEqual(1, result["persistence"]["revision"])
            context = self.load_context(context_path)
            self.assertEqual("project_context_package", context["artifact_type"])
            self.assertEqual("local_file", context["storage"])
            self.assertEqual("disabled", context["external_services"])
            self.assertEqual(
                "SYNTHETIC-PROJECT-A", context["project_id"]
            )
            self.assertEqual(
                ["FACT-001"],
                [item["fact_id"] for item in context["confirmed_facts"]],
            )
            self.assertEqual(
                ["REL-GOVERNS"],
                [
                    item["relation_id"]
                    for item in context["confirmed_relationships"]
                ],
            )
            self.assertTrue(
                all(
                    item["confirmation_status"] == "confirmed"
                    for key in (
                        "confirmed_facts",
                        "confirmed_relationships",
                        "decisions",
                        "conclusions",
                        "trace_links",
                    )
                    for item in context[key]
                )
            )

    def test_rejected_and_pending_updates_do_not_create_or_change_context(self):
        with tempfile.TemporaryDirectory() as directory:
            context_path = Path(directory) / "project-context.json"
            initial = self.run_request(
                deepcopy(self.fixture["confirmed_update"]),
                context_path,
            )
            self.assertEqual(0, initial.returncode, initial.stderr)
            original_bytes = context_path.read_bytes()

            for status in ("rejected", "pending"):
                with self.subTest(status=status):
                    request = deepcopy(self.fixture["upstream_change"])
                    request["confirmation"]["status"] = status
                    completed = self.run_request(request, context_path)

                    self.assertEqual(0, completed.returncode, completed.stderr)
                    result = json.loads(completed.stdout)
                    self.assertEqual(status, result["persistence"]["status"])
                    self.assertEqual(original_bytes, context_path.read_bytes())

    def test_upstream_change_marks_dependent_conclusions_and_traces_for_review(self):
        with tempfile.TemporaryDirectory() as directory:
            context_path = Path(directory) / "project-context.json"
            initial = self.run_request(
                deepcopy(self.fixture["confirmed_update"]),
                context_path,
            )
            self.assertEqual(0, initial.returncode, initial.stderr)

            changed = self.run_request(
                deepcopy(self.fixture["upstream_change"]),
                context_path,
            )

            self.assertEqual(0, changed.returncode, changed.stderr)
            result = json.loads(changed.stdout)
            invalidated = result["persistence"]["invalidated"]
            self.assertEqual(["MAT-UPSTREAM"], invalidated["material_ids"])
            self.assertEqual(
                ["CONCLUSION-001"], invalidated["conclusion_ids"]
            )
            self.assertEqual(["TRACE-001"], invalidated["trace_ids"])
            self.assertEqual(["DECISION-001"], invalidated["decision_ids"])
            self.assertEqual(["REL-GOVERNS"], invalidated["relation_ids"])

            context = self.load_context(context_path)
            self.assertEqual(2, context["revision"])
            for key in (
                "confirmed_relationships",
                "decisions",
                "conclusions",
                "trace_links",
            ):
                self.assertEqual("pending_review", context[key][0]["review_status"])
                self.assertEqual(
                    ["MAT-UPSTREAM"],
                    context[key][0]["stale_due_to_material_ids"],
                )

    def test_context_rejects_cross_project_update_without_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            context_path = Path(directory) / "project-context.json"
            initial = self.run_request(
                deepcopy(self.fixture["confirmed_update"]),
                context_path,
            )
            self.assertEqual(0, initial.returncode, initial.stderr)
            original_bytes = context_path.read_bytes()
            request = deepcopy(self.fixture["upstream_change"])
            request["project_id"] = "SYNTHETIC-PROJECT-B"

            completed = self.run_request(request, context_path)

            self.assertEqual(1, completed.returncode)
            error = json.loads(completed.stderr)
            self.assertEqual("project_isolation_violation", error["error"])
            self.assertEqual(original_bytes, context_path.read_bytes())

    def test_secret_account_and_unnecessary_personal_data_are_not_persisted(self):
        unsafe_values = [
            ("api_token", "ghp_0123456789abcdefghijklmnopqrstuvwxyz"),
            ("text", "测试联系人邮箱为 user@example.com"),
            ("text", "真实账号为 project-admin"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for index, (field, value) in enumerate(unsafe_values):
                with self.subTest(field=field, value=value):
                    context_path = (
                        Path(directory) / "unsafe-{}.json".format(index)
                    )
                    request = deepcopy(self.fixture["confirmed_update"])
                    request["update"]["facts"][0][field] = value

                    completed = self.run_request(request, context_path)

                    self.assertEqual(1, completed.returncode)
                    error = json.loads(completed.stderr)
                    self.assertEqual(
                        "persistence_rejected_sensitive_data",
                        error["error"],
                    )
                    self.assertNotIn(value, completed.stderr)
                    self.assertNotIn(value, completed.stdout)
                    self.assertFalse(context_path.exists())

    def test_unknown_fields_and_non_user_confirmation_are_rejected(self):
        invalid_requests = []
        unknown = deepcopy(self.fixture["confirmed_update"])
        unknown["upload_url"] = "https://example.invalid"
        invalid_requests.append((unknown, "unknown_fields"))

        non_user = deepcopy(self.fixture["confirmed_update"])
        non_user["confirmation"]["actor"] = "model"
        invalid_requests.append((non_user, "actor"))

        with tempfile.TemporaryDirectory() as directory:
            for index, (request, expected) in enumerate(invalid_requests):
                with self.subTest(expected=expected):
                    context_path = (
                        Path(directory) / "invalid-{}.json".format(index)
                    )
                    completed = self.run_request(request, context_path)

                    self.assertEqual(1, completed.returncode)
                    error = json.loads(completed.stderr)
                    self.assertEqual("invalid_request", error["error"])
                    self.assertIn(expected, error["message"])
                    self.assertFalse(context_path.exists())

    def test_runtime_has_no_network_or_external_database_imports(self):
        text = SCRIPT.read_text(encoding="utf-8")
        for token in (
            "urllib",
            "requests",
            "http.client",
            "socket",
            "sqlite3",
            "sqlalchemy",
        ):
            self.assertNotIn(token, text)


if __name__ == "__main__":
    unittest.main()
