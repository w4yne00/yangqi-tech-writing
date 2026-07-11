import sys
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from evidence_check import validate_ledger


class EvidenceCheckTests(unittest.TestCase):
    def test_supported_and_opinion_pass(self):
        report = validate_ledger({"claims": [
            {"claim_id": "C-1", "status": "SUPPORTED", "risk": "high", "source_ref": "需求书3.2"},
            {"claim_id": "C-2", "status": "OPINION", "risk": "medium", "source_ref": "方案建议"},
        ]})
        self.assertTrue(report["passed"])

    def test_high_risk_unsupported_blocks(self):
        report = validate_ledger({"claims": [
            {"claim_id": "C-3", "status": "UNSUPPORTED", "risk": "high", "source_ref": ""}
        ]})
        self.assertFalse(report["passed"])
        self.assertEqual(["C-3"], report["blockers"])

    def test_invalid_status_is_schema_error(self):
        report = validate_ledger({"claims": [
            {"claim_id": "C-4", "status": "VERIFIED", "risk": "low", "source_ref": "附件"}
        ]})
        self.assertIn("C-4: invalid status VERIFIED", report["errors"])


if __name__ == "__main__":
    unittest.main()
