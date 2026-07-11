#!/usr/bin/env python3
"""Compare protected spans before and after rewriting."""

import argparse
import json
import re
from pathlib import Path


PATTERNS = {
    "policy_id": re.compile(r"[\u4e00-\u9fff]{2,14}(?:〔|\[)\d{4}(?:〕|\])\d+号"),
    "standard_id": re.compile(r"(?:GB/T|GB|GM/T|ISO/IEC|ISO)\s*[0-9A-Z.]+(?:[—-]\d{4})?"),
    "amount": re.compile(r"\d+(?:\.\d+)?(?:万|亿)?元"),
    "percentage": re.compile(r"\d+(?:\.\d+)?%"),
    "date": re.compile(r"\d{4}年\d{1,2}月(?:\d{1,2}日)?"),
    "recovery_metric": re.compile(r"(?:RTO|RPO)为?\d+(?:\.\d+)?(?:秒|分钟|小时|天)"),
    "responsible_party": re.compile(
        r"(?:建设方|承建方|监理方|运营方|投标人|招标人|"
        r"信息科技部门|网络安全管理部门|所属单位)"
    ),
}

NORMATIVE_TERMS = ("应", "须", "不得", "可", "负责", "承担")
POLICY_CONTEXT_PREFIXES = ("根据", "依据", "按照")


def _unique(items):
    return list(dict.fromkeys(items))


def _clean_policy_id(value: str) -> str:
    for prefix in POLICY_CONTEXT_PREFIXES:
        if value.startswith(prefix):
            return value[len(prefix):]
    return value


def extract_protected(text: str) -> dict:
    result = {}
    for name, pattern in PATTERNS.items():
        values = [match.group(0) for match in pattern.finditer(text)]
        if name == "policy_id":
            values = [_clean_policy_id(value) for value in values]
        result[name] = _unique(values)
    return result


def compare_texts(before: str, after: str) -> dict:
    before_items = extract_protected(before)
    after_items = extract_protected(after)
    missing = {
        name: [item for item in values if item not in after_items[name]]
        for name, values in before_items.items()
    }
    missing = {name: values for name, values in missing.items() if values}
    normative_changes = {
        term: {"before": before.count(term), "after": after.count(term)}
        for term in NORMATIVE_TERMS
        if before.count(term) != after.count(term)
    }
    return {
        "passed": not missing and not normative_changes,
        "missing": missing,
        "normative_changes": normative_changes,
        "before": before_items,
        "after": after_items,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("before")
    parser.add_argument("after")
    args = parser.parse_args()
    try:
        before = Path(args.before).read_text(encoding="utf-8")
        after = Path(args.after).read_text(encoding="utf-8")
    except OSError as exc:
        print(json.dumps({"passed": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    report = compare_texts(before, after)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
