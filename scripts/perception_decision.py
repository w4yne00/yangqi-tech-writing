#!/usr/bin/env python3
"""Build the minimum observable perception decision for a material task."""

import argparse
import json
from pathlib import Path
import re
import sys


SCHEMA_VERSION = "1.0"

CONTENT_CONTRACTS = [
    "common.protected_spans",
    "common.evidence_policy",
]
QUALITY_CONTRACTS = [
    "common.quality_gate_h1_h6",
]
COMMON_CONTRACTS = CONTENT_CONTRACTS + QUALITY_CONTRACTS
ARCHITECTURE_DESIGN_CONTRACTS = (
    CONTENT_CONTRACTS + ["scene.architecture_design"] + QUALITY_CONTRACTS
)

PRELIMINARY_DESIGN_SIGNALS = ("初步设计", "初设")
NEGATED_PRELIMINARY_DESIGN_PATTERNS = (
    re.compile(
        r"(?:不是|不属于|并非|不能认定为|不应认定为|不能视为|"
        r"尚未确认为|未确认为|非)\s*(?:初步设计|初设)"
    ),
    re.compile(
        r"(?:初步设计|初设)\s*(?:的)?\s*"
        r"(?:材料|文种|类型|子类型|分类)?\s*"
        r"(?:尚未确认|未确认|待确认|尚不明确|不明确)"
    ),
)
DESIGN_SIGNALS = ("设计",)


class RequestError(ValueError):
    """The request does not satisfy the public input contract."""


def classification(value, confidence, candidates=None):
    """Return one classification dimension in the public decision shape."""
    return {
        "value": value,
        "confidence": confidence,
        "candidates": candidates or [],
    }


def candidate(value, basis):
    return {"value": value, "basis": basis}


def has_negated_preliminary_design_signal(text):
    return any(
        pattern.search(text)
        for pattern in NEGATED_PRELIMINARY_DESIGN_PATTERNS
    )


def require_mapping(value, field):
    if not isinstance(value, dict):
        raise RequestError("{} 必须是对象".format(field))
    return value


def require_text(mapping, field):
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        raise RequestError("{} 必须是非空字符串".format(field))
    return value.strip()


def validate_material_view(raw_view):
    view = require_mapping(raw_view, "material_view")
    if view.get("schema_version") != SCHEMA_VERSION:
        raise RequestError("material_view.schema_version 必须为 {}".format(SCHEMA_VERSION))
    if view.get("view_type") != "material_normalized_view":
        raise RequestError(
            "material_view.view_type 必须为 material_normalized_view"
        )
    if view.get("is_formal_material") is not False:
        raise RequestError("材料标准化视图不是新的正式材料")

    source_id = require_text(view, "source_id")
    material_status = require_text(view, "material_status")
    title = require_text(view, "title")

    segments = view.get("segments")
    if not isinstance(segments, list) or not segments:
        raise RequestError("material_view.segments 必须至少包含一个定位片段")

    texts = [title]
    locator = None
    for index, segment in enumerate(segments):
        segment = require_mapping(
            segment, "material_view.segments[{}]".format(index)
        )
        text = segment.get("text")
        if isinstance(text, str):
            texts.append(text)
        raw_locator = segment.get("locator")
        if raw_locator is None:
            continue
        candidate_locator = require_mapping(
            raw_locator,
            "material_view.segments[{}].locator".format(index),
        )
        has_usable_locator = any(
            isinstance(value, (str, int, float))
            and not isinstance(value, bool)
            and str(value).strip()
            for value in candidate_locator.values()
        )
        if locator is None and has_usable_locator:
            locator = candidate_locator

    if locator is None:
        raise RequestError("material_view.segments 缺少可用的最小定位")

    return {
        "source_id": source_id,
        "material_status": material_status,
        "title": title,
        "locator": locator,
        "searchable_text": "\n".join(texts),
    }


def validate_task(raw_task):
    task = require_mapping(raw_task, "task")
    instruction = require_text(task, "instruction")
    mode = require_text(task, "mode")
    if mode not in {"create", "continue", "rewrite", "review", "annotation"}:
        raise RequestError("task.mode 不是受支持的任务模式")
    scope = require_text(task, "scope")
    return {"instruction": instruction, "mode": mode, "scope": scope}


def build_explicit_preliminary_design_decision(task):
    supports_review = task["mode"] in {"review", "annotation"}
    quick_review = supports_review and task["scope"] == "local"
    support_level = (
        "basic_support" if supports_review else "recognition_coverage"
    )
    return {
        "business_domain": classification(
            "engineering_construction", "explicit"
        ),
        "lifecycle_position": classification("design", "explicit"),
        "document_scene": classification("architecture_design", "explicit"),
        "material_subtype": classification("preliminary_design", "explicit"),
        "task_mode": task["mode"],
        "support_level": support_level,
        "processing_mode": "quick_path" if quick_review else "conservative_audit",
        "load_contracts": (
            ARCHITECTURE_DESIGN_CONTRACTS
            if supports_review
            else COMMON_CONTRACTS
        ),
        "pending_confirmations": (
            [] if supports_review else ["task_mode_support"]
        ),
        "blockers": [],
    }


def build_unclear_decision(task, text):
    has_design_signal = any(signal in text for signal in DESIGN_SIGNALS)
    domain_candidates = []
    lifecycle_candidates = []
    scene_candidates = []
    if has_design_signal:
        domain_candidates.append(
            candidate(
                "engineering_construction",
                "材料出现设计信号，但不足以排除科研课题或治理运行语境。",
            )
        )
        lifecycle_candidates.append(
            candidate(
                "design",
                "材料出现设计信号，但未明确生命周期位置。",
            )
        )
        scene_candidates.append(
            candidate(
                "architecture_design",
                "材料可能适用架构设计场景，仍需确认具体文种。",
            )
        )

    pending = [
        "business_domain",
        "lifecycle_position",
        "document_scene",
        "material_subtype",
    ]
    return {
        "business_domain": classification(
            "unknown", "unclear", domain_candidates
        ),
        "lifecycle_position": classification(
            "unknown", "unclear", lifecycle_candidates
        ),
        "document_scene": classification(
            "unknown", "unclear", scene_candidates
        ),
        "material_subtype": classification("unknown", "unclear"),
        "task_mode": task["mode"],
        "support_level": "recognition_coverage",
        "processing_mode": "conservative_audit",
        "load_contracts": COMMON_CONTRACTS,
        "pending_confirmations": pending,
        "blockers": [],
    }


def build_perception_decision(request):
    """Return the observable decision for one task and normalized view."""
    request = require_mapping(request, "request")
    task = validate_task(request.get("task"))
    view = validate_material_view(request.get("material_view"))
    text = "\n".join(
        [task["instruction"], view["title"], view["searchable_text"]]
    )

    has_preliminary_design_signal = any(
        signal in text for signal in PRELIMINARY_DESIGN_SIGNALS
    )
    has_negated_signal = has_negated_preliminary_design_signal(text)
    if has_preliminary_design_signal and not has_negated_signal:
        decision = build_explicit_preliminary_design_decision(task)
    else:
        decision = build_unclear_decision(task, text)

    return {
        "schema_version": SCHEMA_VERSION,
        "material_view": {
            "source_id": view["source_id"],
            "material_status": view["material_status"],
            "locator": view["locator"],
            "is_formal_material": False,
            "view_role": "derived_normalized_view",
        },
        "decision": decision,
    }


def read_request(path):
    if path == "-":
        return json.load(sys.stdin)
    with Path(path).open(encoding="utf-8") as handle:
        return json.load(handle)


def main():
    parser = argparse.ArgumentParser(
        description="生成材料任务的最小感知与处理决策。"
    )
    parser.add_argument("request", help="请求 JSON 文件；使用 - 从标准输入读取")
    args = parser.parse_args()

    try:
        result = build_perception_decision(read_request(args.request))
    except (OSError, json.JSONDecodeError, RequestError) as exc:
        print(
            json.dumps(
                {"error": "invalid_request", "message": str(exc)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
