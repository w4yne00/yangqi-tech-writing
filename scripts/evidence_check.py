#!/usr/bin/env python3
"""Validate an evidence ledger."""

import argparse
import json
from pathlib import Path


VALID_STATUSES = {
    "SUPPORTED",
    "OPINION",
    "UNSUPPORTED",
    "CONTRADICTED",
    "NEEDS_USER_CONFIRMATION",
}
VALID_RISKS = {"low", "medium", "high"}


def validate_ledger(ledger: dict) -> dict:
    errors = []
    warnings = []
    blockers = []
    if not isinstance(ledger, dict) or not isinstance(ledger.get("claims"), list):
        return {
            "passed": False,
            "errors": ["ledger.claims must be an array"],
            "warnings": [],
            "blockers": [],
        }

    seen = set()
    for index, claim in enumerate(ledger["claims"], start=1):
        if not isinstance(claim, dict):
            errors.append("claim %d must be an object" % index)
            continue
        claim_id = str(claim.get("claim_id", "")).strip()
        status = str(claim.get("status", "")).strip()
        risk = str(claim.get("risk", "")).strip()
        source_ref = str(claim.get("source_ref", "")).strip()
        if not claim_id:
            errors.append("claim %d: missing claim_id" % index)
            continue
        if claim_id in seen:
            errors.append("%s: duplicate claim_id" % claim_id)
        seen.add(claim_id)
        if status not in VALID_STATUSES:
            errors.append("%s: invalid status %s" % (claim_id, status))
            continue
        if risk not in VALID_RISKS:
            errors.append("%s: invalid risk %s" % (claim_id, risk))
            continue
        if status == "SUPPORTED" and not source_ref:
            errors.append("%s: SUPPORTED requires source_ref" % claim_id)
        if status in {"CONTRADICTED", "NEEDS_USER_CONFIRMATION"}:
            blockers.append(claim_id)
        elif status == "UNSUPPORTED" and risk == "high":
            blockers.append(claim_id)
        elif status == "UNSUPPORTED":
            warnings.append("%s: unsupported %s-risk claim" % (claim_id, risk))

    return {
        "passed": not errors and not blockers,
        "errors": errors,
        "warnings": warnings,
        "blockers": blockers,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("ledger")
    args = parser.parse_args()
    try:
        ledger = json.loads(Path(args.ledger).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(json.dumps({"passed": False, "errors": [str(exc)]}, ensure_ascii=False, indent=2))
        return 1
    report = validate_ledger(ledger)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["errors"]:
        return 1
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
