#!/usr/bin/env python3
"""Build the observable perception decision for a material task."""

import argparse
import json
from pathlib import Path
import re
import sys


SCHEMA_VERSION = "1.0"

CONTENT_CONTRACTS = [
    "common.protected_spans",
    "common.evidence_policy",
    "common.statement_force_policy",
]
QUALITY_CONTRACTS = [
    "common.quality_gate_h1_h6",
]
COMMON_CONTRACTS = CONTENT_CONTRACTS + QUALITY_CONTRACTS
PRELIMINARY_DESIGN_SIGNALS = ("初步设计", "初设")
ENGINEERING_MATERIAL_ROUTES = (
    {
        "signals": ("项目建议书",),
        "lifecycle_position": "initiation",
        "document_scene": "feasibility_study",
        "material_subtype": "project_proposal",
    },
    {
        "signals": ("可行性研究报告", "工程可研报告", "可研报告"),
        "lifecycle_position": "initiation",
        "document_scene": "feasibility_study",
        "material_subtype": "feasibility_study",
    },
    {
        "signals": PRELIMINARY_DESIGN_SIGNALS,
        "lifecycle_position": "design",
        "document_scene": "architecture_design",
        "material_subtype": "preliminary_design",
    },
    {
        "signals": ("详细设计", "详设"),
        "lifecycle_position": "design",
        "document_scene": "architecture_design",
        "material_subtype": "detailed_design",
    },
    {
        "signals": ("总体架构设计", "总体架构"),
        "lifecycle_position": "design",
        "document_scene": "architecture_design",
        "material_subtype": "overall_architecture",
    },
    {
        "signals": ("技术规范书", "招标技术要求", "采购技术要求"),
        "lifecycle_position": "procurement",
        "document_scene": "technical_spec",
        "material_subtype": "technical_specification",
    },
    {
        "signals": ("投标技术应答", "投标应答", "技术应答文件"),
        "lifecycle_position": "procurement",
        "document_scene": "bid_response",
        "material_subtype": "bid_response",
    },
    {
        "signals": ("工程实施方案",),
        "lifecycle_position": "implementation",
        "document_scene": "architecture_design",
        "material_subtype": "engineering_implementation_plan",
    },
    {
        "signals": ("工程实施记录",),
        "lifecycle_position": "implementation",
        "document_scene": "review_acceptance",
        "material_subtype": "implementation_record",
    },
    {
        "signals": (
            "工程建设阶段汇报",
            "工程阶段汇报",
            "项目实施阶段汇报",
        ),
        "lifecycle_position": "implementation",
        "document_scene": "presentation",
        "material_subtype": "stage_report",
    },
    {
        "signals": ("工程试运行报告", "试运行报告"),
        "lifecycle_position": "trial_run",
        "document_scene": "review_acceptance",
        "material_subtype": "trial_run_report",
    },
    {
        "signals": ("工程运行维护报告", "工程运营报告"),
        "lifecycle_position": "operation",
        "document_scene": "presentation",
        "material_subtype": "operation_report",
    },
    {
        "signals": ("工程验收大纲",),
        "lifecycle_position": "acceptance",
        "document_scene": "review_acceptance",
        "material_subtype": "acceptance_outline",
    },
    {
        "signals": ("工程验收报告",),
        "lifecycle_position": "acceptance",
        "document_scene": "review_acceptance",
        "material_subtype": "acceptance_report",
    },
)
RESEARCH_MATERIAL_ROUTES = (
    {
        "signals": (
            "科研课题申报书",
            "科研项目申报书",
            "科研申报书",
            "课题申报书",
        ),
        "lifecycle_position": "application",
        "document_scene": "feasibility_study",
        "material_subtype": "research_application",
    },
    {
        "signals": (
            "科研课题可行性论证报告",
            "科研项目可行性论证报告",
            "科研可行性论证报告",
            "课题可行性论证报告",
            "科研课题可行性论证",
            "科研项目可行性论证",
            "科研可行性论证",
            "课题可行性论证",
            "科研课题可研论证报告",
            "科研可研论证报告",
            "课题可研论证报告",
            "科研课题可研论证",
            "科研项目可研论证",
            "科研可研论证",
            "课题可研论证",
        ),
        "lifecycle_position": "application",
        "document_scene": "feasibility_study",
        "material_subtype": "research_feasibility_assessment",
    },
    {
        "signals": (
            "科研课题任务书",
            "科研项目任务书",
            "科研任务书",
            "课题任务书",
        ),
        "lifecycle_position": "task_agreement",
        "document_scene": "technical_spec",
        "material_subtype": "research_task_agreement",
    },
    {
        "signals": (
            "科研课题研究实施方案",
            "科研项目研究实施方案",
            "科研研究实施方案",
            "科研实施方案",
            "课题研究实施方案",
            "研究实施方案",
        ),
        "lifecycle_position": "research_implementation",
        "document_scene": "architecture_design",
        "material_subtype": "research_implementation_plan",
    },
    {
        "signals": (
            "科研课题中期汇报",
            "科研项目中期汇报",
            "科研中期汇报",
            "课题中期汇报",
        ),
        "lifecycle_position": "midterm_review",
        "document_scene": "presentation",
        "material_subtype": "research_interim_report",
    },
    {
        "signals": (
            "科研课题中期检查报告",
            "科研项目中期检查报告",
            "科研中期检查报告",
            "课题中期检查报告",
            "科研课题中期检查",
            "科研项目中期检查",
            "科研中期检查",
            "课题中期检查",
        ),
        "lifecycle_position": "midterm_review",
        "document_scene": "review_acceptance",
        "material_subtype": "research_interim_inspection",
    },
    {
        "signals": (
            "科研课题结题验收材料",
            "科研项目结题验收材料",
            "科研结题验收材料",
            "课题结题验收材料",
            "结题验收材料",
            "科研课题结题验收报告",
            "科研项目结题验收报告",
            "科研结题验收报告",
            "课题结题验收报告",
            "结题验收报告",
        ),
        "lifecycle_position": "final_acceptance",
        "document_scene": "review_acceptance",
        "material_subtype": "research_final_acceptance",
    },
)
RESEARCH_CONTEXTUAL_SIGNALS = {
    "research_application": ("申报书",),
    "research_feasibility_assessment": (
        "可研论证",
        "可研论证报告",
        "可行性论证",
        "可行性论证报告",
    ),
    "research_task_agreement": ("任务书",),
    "research_implementation_plan": ("实施方案",),
    "research_interim_report": ("中期汇报", "中期阶段汇报"),
    "research_interim_inspection": ("中期检查", "中期检查报告"),
    "research_final_acceptance": ("结题验收材料", "结题验收报告"),
}
RESEARCH_CONTEXT_PATTERN = r"(?:科研(?:课题)?|课题)"
NEGATED_RESEARCH_CONTEXT_PATTERNS = (
    re.compile(
        r"(?:不是|不属于|并非|不能认定为|不应认定为|不能视为|"
        r"尚未确认为|未确认为|非)\s*"
        + RESEARCH_CONTEXT_PATTERN
        + r"(?:材料|项目|语境)?"
    ),
)
RESEARCH_QUALIFIED_MATERIAL_SIGNALS = tuple(
    dict.fromkeys(
        signal
        for route in ENGINEERING_MATERIAL_ROUTES
        for signal in route["signals"]
    )
) + ("验收大纲", "验收报告", "阶段汇报", "实施方案")
RESEARCH_QUALIFIED_MATERIAL_PATTERN = "|".join(
    re.escape(signal)
    for signal in sorted(
        RESEARCH_QUALIFIED_MATERIAL_SIGNALS, key=len, reverse=True
    )
)
RESEARCH_MATERIAL_SIGNAL_PATTERN = "|".join(
    re.escape(signal)
    for signal in sorted(
        {
            signal
            for route in RESEARCH_MATERIAL_ROUTES
            for signal in route["signals"]
        }
        | {
            signal
            for signals in RESEARCH_CONTEXTUAL_SIGNALS.values()
            for signal in signals
        },
        key=len,
        reverse=True,
    )
)
RESEARCH_MATERIAL_REFERENCE_PATTERNS = (
    re.compile(
        r"(?:依据|引用|参照|参考|根据|按照|基于|见)\s*"
        r"(?:了)?(?:某|本|该)?(?:"
        + RESEARCH_MATERIAL_SIGNAL_PATTERN
        + r")"
    ),
)
RESEARCH_AFFILIATION_PATTERNS = (
    re.compile(
        r"(?:本|该|此)?(?:材料|文件|报告|项目|任务|工作)\s*"
        r"(?:属于|归属于|定位为|认定为|确认为|是|为)\s*"
        r"(?:某|本|该)?"
        + RESEARCH_CONTEXT_PATTERN
        + r"(?:材料|项目|语境)?"
    ),
    re.compile(
        RESEARCH_CONTEXT_PATTERN + r"(?:材料|语境)"
    ),
    re.compile(
        RESEARCH_CONTEXT_PATTERN
        + r"(?:项目)?(?:研究实施方案|"
        r"(?:开题|中期|年度|结题)阶段汇报)"
    ),
    re.compile(
        RESEARCH_CONTEXT_PATTERN
        + r"(?:项目)?(?:的)?(?:"
        + RESEARCH_QUALIFIED_MATERIAL_PATTERN
        + r")"
    ),
)
MATERIAL_SUBTYPE_NEGATION_ALIASES = {
    "project_proposal": ("工程立项材料",),
    "feasibility_study": ("工程立项材料",),
    "technical_specification": ("工程采购材料",),
    "bid_response": ("工程采购材料",),
    "engineering_implementation_plan": ("实施方案",),
    "implementation_record": ("实施记录",),
    "stage_report": ("阶段汇报",),
    "trial_run_report": ("工程试运行材料", "试运行材料"),
    "acceptance_outline": ("项目验收大纲", "验收大纲"),
    "acceptance_report": ("项目验收报告", "验收报告"),
    "operation_report": (
        "工程运营材料",
        "工程运行维护材料",
        "运营材料",
    ),
}
SCENE_CONTRACTS = {
    "architecture_design": "scene.architecture_design",
    "bid_response": "scene.bid_response",
    "feasibility_study": "scene.feasibility_study",
    "presentation": "scene.presentation",
    "review_acceptance": "scene.review_acceptance",
    "technical_spec": "scene.technical_spec",
}
DESIGN_SIGNALS = ("设计",)
EVIDENCE_STATUSES = {
    "SUPPORTED",
    "OPINION",
    "UNSUPPORTED",
    "CONTRADICTED",
    "NEEDS_USER_CONFIRMATION",
}
STATEMENT_FORCES = {
    "assumption",
    "professional_judgment",
    "recommended_solution",
    "approved_boundary",
    "contractual_commitment",
    "implementation_fact",
    "acceptance_conclusion",
}
SOURCE_REQUIRED_STATEMENT_FORCES = {
    "approved_boundary",
    "contractual_commitment",
    "implementation_fact",
    "acceptance_conclusion",
}
MATERIAL_RELATION_TYPES = {
    "governs",
    "derives_from",
    "supersedes",
    "implements",
    "verifies",
    "conflicts_with",
    "unclear",
}
MATERIAL_CONFLICT_DIMENSIONS = {
    "scope",
    "quantity",
    "parameter",
    "responsibility",
    "time",
    "conclusion",
    "statement_force",
}
MATERIAL_STATUSES = {
    "draft",
    "approved",
    "signed",
    "effective",
    "superseded",
    "unknown",
}


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


def has_negated_material_signal(text, signals):
    signal_pattern = "|".join(
        re.escape(signal) for signal in sorted(signals, key=len, reverse=True)
    )
    patterns = (
        re.compile(
            r"(?:不是|不属于|并非|不能认定为|不应认定为|不能视为|"
            r"尚未确认为|未确认为|非)\s*(?:{})".format(signal_pattern)
        ),
        re.compile(
            r"(?:{})\s*(?:的)?\s*"
            r"(?:材料|文种|类型|子类型|分类)?\s*"
            r"(?:尚未确认|未确认|待确认|尚不明确|不明确)".format(
                signal_pattern
            )
        ),
    )
    return any(pattern.search(text) for pattern in patterns)


def strip_research_material_references(text):
    remaining_text = text
    for pattern in RESEARCH_MATERIAL_REFERENCE_PATTERNS:
        remaining_text = pattern.sub("", remaining_text)
    return remaining_text


def has_active_research_context(text):
    remaining_text = text
    for pattern in NEGATED_RESEARCH_CONTEXT_PATTERNS:
        remaining_text = pattern.sub("", remaining_text)
    remaining_text = strip_research_material_references(remaining_text)
    return any(
        pattern.search(remaining_text)
        for pattern in RESEARCH_AFFILIATION_PATTERNS
    )


def has_unnegated_research_marker(text):
    remaining_text = text
    for pattern in NEGATED_RESEARCH_CONTEXT_PATTERNS:
        remaining_text = pattern.sub("", remaining_text)
    remaining_text = strip_research_material_references(remaining_text)
    return re.search(RESEARCH_CONTEXT_PATTERN, remaining_text) is not None


def has_negated_research_context(text):
    return any(
        pattern.search(text) for pattern in NEGATED_RESEARCH_CONTEXT_PATTERNS
    )


def matching_engineering_routes(text):
    if has_active_research_context(text):
        return []
    return [
        route
        for route in ENGINEERING_MATERIAL_ROUTES
        if any(signal in text for signal in route["signals"])
        and not has_negated_material_signal(text, route["signals"])
    ]


def matching_research_routes(text, include_contextual=False):
    material_text = strip_research_material_references(text)
    has_explicit_engineering_signal = any(
        signal in material_text
        for route in ENGINEERING_MATERIAL_ROUTES
        for signal in route["signals"]
    )
    routes = []
    for route in RESEARCH_MATERIAL_ROUTES:
        signals = route["signals"]
        if include_contextual and not has_explicit_engineering_signal:
            signals = signals + RESEARCH_CONTEXTUAL_SIGNALS.get(
                route["material_subtype"], ()
            )
        if (
            any(signal in material_text for signal in signals)
            and not has_negated_material_signal(material_text, signals)
        ):
            routes.append(route)
    return routes


def resolve_research_identity_routes(task, view):
    """Resolve a research material identity before lower-priority references."""
    material_context = "\n".join(
        [task["instruction"], view["searchable_text"]]
    )
    has_explicit_research_context = has_active_research_context(
        material_context
    )
    title_routes = matching_research_routes(
        view["title"], include_contextual=has_explicit_research_context
    )
    if title_routes:
        if has_negated_research_context(task["instruction"]):
            return matching_research_routes(
                task["instruction"], include_contextual=True
            )
        remaining_title_routes = [
            route
            for route in title_routes
            if not has_negated_material_signal(
                task["instruction"], route["signals"]
            )
        ]
        if remaining_title_routes:
            return remaining_title_routes
        return matching_research_routes(
            task["instruction"],
            include_contextual=has_explicit_research_context,
        )

    for text in (task["instruction"], view["searchable_text"]):
        routes = matching_research_routes(
            text, include_contextual=has_explicit_research_context
        )
        if routes:
            return routes
    return []


def resolve_engineering_identity_routes(task, view):
    """Resolve material identity before considering lower-priority references."""
    material_context = "\n".join(
        [task["instruction"], view["searchable_text"]]
    )
    if has_active_research_context(material_context):
        return []

    title_routes = matching_engineering_routes(view["title"])
    if title_routes:
        remaining_title_routes = [
            route
            for route in title_routes
            if not has_negated_material_signal(
                task["instruction"], route["signals"]
            )
        ]
        if remaining_title_routes:
            return remaining_title_routes
        return matching_engineering_routes(task["instruction"])

    for text in (task["instruction"], view["searchable_text"]):
        routes = matching_engineering_routes(text)
        if routes:
            return routes
    return []


def unique_candidates(items):
    unique = []
    values = set()
    for item in items:
        if item["value"] not in values:
            unique.append(item)
            values.add(item["value"])
    return unique


def is_material_subtype_negated(text, material_subtype):
    signals = []
    for route in ENGINEERING_MATERIAL_ROUTES + RESEARCH_MATERIAL_ROUTES:
        if route["material_subtype"] == material_subtype:
            signals.extend(route["signals"])
            signals.extend(
                RESEARCH_CONTEXTUAL_SIGNALS.get(material_subtype, ())
            )
    signals.extend(
        MATERIAL_SUBTYPE_NEGATION_ALIASES.get(material_subtype, ())
    )
    return bool(signals) and has_negated_material_signal(text, signals)


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

    texts = []
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


def validate_claims(raw_claims):
    if raw_claims is None:
        return []
    if not isinstance(raw_claims, list):
        raise RequestError("claims 必须是数组")

    claims = []
    seen_claim_ids = set()
    for index, raw_claim in enumerate(raw_claims):
        field = "claims[{}]".format(index)
        claim = require_mapping(raw_claim, field)
        claim_id = require_text(claim, "claim_id")
        if claim_id in seen_claim_ids:
            raise RequestError("claims.claim_id 不得重复: {}".format(claim_id))
        seen_claim_ids.add(claim_id)

        text = require_text(claim, "text")
        evidence_status = require_text(claim, "evidence_status")
        if evidence_status not in EVIDENCE_STATUSES:
            raise RequestError(
                "{}.evidence_status 不是受支持的证据状态".format(field)
            )

        statement_force = require_text(claim, "statement_force")
        if (
            statement_force not in STATEMENT_FORCES
            and statement_force != "unknown"
        ):
            raise RequestError(
                "{}.statement_force 不是受支持的陈述效力".format(field)
            )

        requested_force = claim.get(
            "requested_statement_force", statement_force
        )
        if (
            not isinstance(requested_force, str)
            or (
                requested_force not in STATEMENT_FORCES
                and requested_force != "unknown"
            )
        ):
            raise RequestError(
                "{}.requested_statement_force 不是受支持的陈述效力".format(
                    field
                )
            )

        raw_source_ref = claim.get("source_ref", "")
        source_ref = (
            raw_source_ref.strip()
            if isinstance(raw_source_ref, str)
            else ""
        )
        if evidence_status == "SUPPORTED" and not source_ref:
            raise RequestError(
                "{}.source_ref 是 SUPPORTED 陈述的必填项".format(field)
            )

        claims.append(
            {
                "claim_id": claim_id,
                "text": text,
                "evidence_status": evidence_status,
                "statement_force": statement_force,
                "requested_statement_force": requested_force,
                "source_ref": source_ref,
            }
        )
    return claims


def validate_material_set(raw_material_set):
    if raw_material_set is None:
        return None
    material_set = require_mapping(raw_material_set, "material_set")
    set_id = require_text(material_set, "set_id")
    upstream_materials_complete = material_set.get(
        "upstream_materials_complete"
    )
    if not isinstance(upstream_materials_complete, bool):
        raise RequestError(
            "material_set.upstream_materials_complete 必须是布尔值"
        )

    raw_materials = material_set.get("materials")
    if not isinstance(raw_materials, list) or not raw_materials:
        raise RequestError("material_set.materials 必须至少包含一份材料")

    materials = []
    material_ids = set()
    for index, raw_material in enumerate(raw_materials):
        field = "material_set.materials[{}]".format(index)
        material = require_mapping(raw_material, field)
        material_id = require_text(material, "material_id")
        if material_id in material_ids:
            raise RequestError(
                "material_set.material_id 不得重复: {}".format(material_id)
            )
        material_ids.add(material_id)
        date = material.get("date")
        if date is not None and (
            not isinstance(date, str) or not date.strip()
        ):
            raise RequestError("{}.date 必须是非空字符串".format(field))
        user_designated_control = material.get(
            "user_designated_control", False
        )
        if not isinstance(user_designated_control, bool):
            raise RequestError(
                "{}.user_designated_control 必须是布尔值".format(field)
            )
        status = require_text(material, "status")
        if status not in MATERIAL_STATUSES:
            raise RequestError(
                "{}.status 不是受支持的材料状态".format(field)
            )
        materials.append(
            {
                "material_id": material_id,
                "title": require_text(material, "title"),
                "version": require_text(material, "version"),
                "material_subtype": require_text(
                    material, "material_subtype"
                ),
                "status": status,
                "date": date.strip() if isinstance(date, str) else None,
                "user_designated_control": user_designated_control,
            }
        )

    raw_relations = material_set.get("relations")
    if not isinstance(raw_relations, list):
        raise RequestError("material_set.relations 必须是数组")

    relationships = []
    relation_ids = set()
    relationship_by_id = {}
    for index, raw_relation in enumerate(raw_relations):
        field = "material_set.relations[{}]".format(index)
        relation = require_mapping(raw_relation, field)
        relation_id = require_text(relation, "relation_id")
        if relation_id in relation_ids:
            raise RequestError(
                "material_set.relation_id 不得重复: {}".format(relation_id)
            )
        relation_ids.add(relation_id)
        from_material_id = require_text(relation, "from_material_id")
        to_material_id = require_text(relation, "to_material_id")
        for material_id in (from_material_id, to_material_id):
            if material_id not in material_ids:
                raise RequestError(
                    "{} 引用了不存在的材料: {}".format(field, material_id)
                )
        relation_type = require_text(relation, "relation_type")
        if relation_type not in MATERIAL_RELATION_TYPES:
            raise RequestError(
                "{}.relation_type 不是受支持的材料关系".format(field)
            )
        normalized_relationship = {
            "relation_id": relation_id,
            "from_material_id": from_material_id,
            "to_material_id": to_material_id,
            "relation_type": relation_type,
            "basis": require_text(relation, "basis"),
        }
        relationships.append(normalized_relationship)
        relationship_by_id[relation_id] = normalized_relationship

    raw_conflicts = material_set.get("conflicts", [])
    if not isinstance(raw_conflicts, list):
        raise RequestError("material_set.conflicts 必须是数组")
    conflicts = []
    conflict_ids = set()
    for index, raw_conflict in enumerate(raw_conflicts):
        field = "material_set.conflicts[{}]".format(index)
        conflict = require_mapping(raw_conflict, field)
        conflict_id = require_text(conflict, "conflict_id")
        if conflict_id in conflict_ids:
            raise RequestError(
                "material_set.conflict_id 不得重复: {}".format(conflict_id)
            )
        conflict_ids.add(conflict_id)
        left_material_id = require_text(conflict, "left_material_id")
        right_material_id = require_text(conflict, "right_material_id")
        for material_id in (left_material_id, right_material_id):
            if material_id not in material_ids:
                raise RequestError(
                    "{} 引用了不存在的材料: {}".format(field, material_id)
                )
        dimension = require_text(conflict, "dimension")
        if dimension not in MATERIAL_CONFLICT_DIMENSIONS:
            raise RequestError(
                "{}.dimension 不是受支持的冲突维度".format(field)
            )
        raw_relation_id = conflict.get("relation_id")
        relation_id = None
        if raw_relation_id is not None:
            relation_id = require_text(conflict, "relation_id")
            relationship = relationship_by_id.get(relation_id)
            if (
                relationship is None
                or relationship["relation_type"] != "conflicts_with"
            ):
                raise RequestError(
                    "{}.relation_id 必须引用 conflicts_with 关系".format(
                        field
                    )
                )
            relationship_material_ids = {
                relationship["from_material_id"],
                relationship["to_material_id"],
            }
            if relationship_material_ids != {
                left_material_id,
                right_material_id,
            }:
                raise RequestError(
                    "{}.relation_id 与冲突材料不一致".format(field)
                )
        normalized_conflict = {
            "conflict_id": conflict_id,
            "material_ids": [
                left_material_id,
                right_material_id,
            ],
            "dimension": dimension,
            "difference": require_text(conflict, "difference"),
            "impact": require_text(conflict, "impact"),
            "pending_confirmation": require_text(
                conflict, "pending_confirmation"
            ),
        }
        if relation_id is not None:
            normalized_conflict["relation_id"] = relation_id
        conflicts.append(normalized_conflict)

    return {
        "set_id": set_id,
        "upstream_materials_complete": upstream_materials_complete,
        "materials": materials,
        "relationships": relationships,
        "conflicts": conflicts,
    }


def build_material_set_review(material_set):
    pending = []
    blockers = []
    control_bases = {
        material["material_id"]: []
        for material in material_set["materials"]
    }
    for material in material_set["materials"]:
        if material["status"] in {"approved", "signed"}:
            control_bases[material["material_id"]].append(
                "formal_status:{}".format(material["status"])
            )
        if material["user_designated_control"]:
            control_bases[material["material_id"]].append(
                "user_designated"
            )
    for relationship in material_set["relationships"]:
        if (
            relationship["relation_type"] == "governs"
            and relationship["from_material_id"]
            != relationship["to_material_id"]
        ):
            control_bases[relationship["from_material_id"]].append(
                "relation:governs:{}".format(
                    relationship["relation_id"]
                )
            )
    control_materials = [
        {
            "material_id": material["material_id"],
            "control_bases": control_bases[material["material_id"]],
        }
        for material in material_set["materials"]
        if control_bases[material["material_id"]]
    ]
    review_conflicts = list(material_set["conflicts"])
    conflict_relation_ids = {
        conflict["relation_id"]
        for conflict in material_set["conflicts"]
        if "relation_id" in conflict
    }
    for relationship in material_set["relationships"]:
        relation_type = relationship["relation_type"]
        relation_id = relationship["relation_id"]
        if relation_type in {"conflicts_with", "unclear"}:
            pending.append("material_relation:{}".format(relation_id))
            blockers.append("material_relation:{}".format(relation_id))
        if relation_type == "conflicts_with":
            if relation_id not in conflict_relation_ids:
                review_conflicts.append(
                    {
                        "conflict_id": "relation:{}".format(
                            relation_id
                        ),
                        "material_ids": [
                            relationship["from_material_id"],
                            relationship["to_material_id"],
                        ],
                        "dimension": "unclear",
                        "difference": relationship["basis"],
                        "impact": "not_provided",
                        "pending_confirmation": (
                            "provide_conflict_dimension_and_impact"
                        ),
                    }
                )
    for conflict in material_set["conflicts"]:
        item = "material_conflict:{}".format(conflict["conflict_id"])
        pending.append(item)
        blockers.append(item)
    if (
        len(material_set["materials"]) >= 2
        and not material_set["relationships"]
    ):
        pending.append("material_set:missing_relationships")
        blockers.append("material_set:missing_relationships")
    cross_material_ids = set()
    for relationship in material_set["relationships"]:
        from_material_id = relationship["from_material_id"]
        to_material_id = relationship["to_material_id"]
        if from_material_id != to_material_id:
            cross_material_ids.update(
                {from_material_id, to_material_id}
            )
    if len(material_set["materials"]) >= 2:
        for material in material_set["materials"]:
            material_id = material["material_id"]
            if material_id not in cross_material_ids:
                item = "material_set:unrelated_material:{}".format(
                    material_id
                )
                pending.append(item)
                blockers.append(item)
    if not material_set["upstream_materials_complete"]:
        pending.append("material_set:missing_upstream")
        blockers.append("material_set:missing_upstream")
    elif len(material_set["materials"]) < 2:
        pending.append("material_set:insufficient_materials")
        blockers.append("material_set:insufficient_materials")

    if not material_set["upstream_materials_complete"]:
        cross_stage_consistency = {
            "status": "not_verifiable",
            "reason": "missing_upstream_materials",
        }
    elif len(material_set["materials"]) < 2:
        cross_stage_consistency = {
            "status": "not_verifiable",
            "reason": "insufficient_materials_for_cross_stage_review",
        }
    elif blockers:
        cross_stage_consistency = {
            "status": "blocked",
            "reason": "unresolved_relationships_or_conflicts",
        }
    else:
        cross_stage_consistency = {
            "status": "reviewable",
            "reason": "upstream_materials_declared_complete",
        }

    review = {
        "mode": "material_set",
        "set_id": material_set["set_id"],
        "precedence_policy": "explicit_relationships_only",
        "materials": material_set["materials"],
        "relationships": material_set["relationships"],
        "control_materials": control_materials,
        "conflicts": review_conflicts,
        "adjudication_policy": "report_only_user_confirmation_required",
        "cross_stage_consistency": cross_stage_consistency,
        "completion_claim": "not_completed",
        "review_status": "blocked" if blockers else "reviewable",
    }
    return review, pending, blockers


def build_single_material_review():
    return {
        "mode": "single_material",
        "precedence_policy": "explicit_relationships_only",
        "relationships": [],
        "control_materials": [],
        "conflicts": [],
        "adjudication_policy": "report_only_user_confirmation_required",
        "cross_stage_consistency": {
            "status": "not_verifiable",
            "reason": "missing_upstream_materials",
        },
        "completion_claim": "not_completed",
        "review_status": "single_material_only",
    }


def decide_claim(claim):
    claim_id = claim["claim_id"]
    evidence_status = claim["evidence_status"]
    source_force = claim["statement_force"]
    requested_force = claim["requested_statement_force"]
    pending = []
    blockers = []

    if source_force == "unknown":
        pending.append("statement_force:{}".format(claim_id))

    if evidence_status == "CONTRADICTED":
        allowed_force = None
        action = "block_conflict"
        blockers.append("claim:{}".format(claim_id))
    elif source_force == "unknown":
        allowed_force = "assumption"
        action = "confirm_and_use_lower_force"
        blockers.append("claim:{}".format(claim_id))
    elif evidence_status == "NEEDS_USER_CONFIRMATION":
        allowed_force = source_force
        action = "confirm_before_finalizing"
        pending.append("evidence:{}".format(claim_id))
        blockers.append("claim:{}".format(claim_id))
    elif (
        evidence_status == "OPINION"
        and source_force in SOURCE_REQUIRED_STATEMENT_FORCES
    ):
        allowed_force = None
        action = "confirm_evidence_force_alignment"
        pending.append("evidence_force:{}".format(claim_id))
        blockers.append("claim:{}".format(claim_id))
    elif evidence_status == "UNSUPPORTED":
        allowed_force = source_force
        action = "require_source"
        if source_force in SOURCE_REQUIRED_STATEMENT_FORCES:
            blockers.append("claim:{}".format(claim_id))
    elif requested_force != source_force:
        allowed_force = source_force
        action = "preserve_source_force"
    else:
        allowed_force = source_force
        action = "preserve"

    return (
        {
            "claim_id": claim_id,
            "evidence_status": evidence_status,
            "source_statement_force": source_force,
            "requested_statement_force": requested_force,
            "allowed_statement_force": allowed_force,
            "action": action,
        },
        pending,
        blockers,
    )


def apply_claim_boundaries(decision, claims):
    claim_decisions = []
    pending = list(decision["pending_confirmations"])
    blockers = list(decision["blockers"])
    for claim in claims:
        claim_decision, claim_pending, claim_blockers = decide_claim(claim)
        claim_decisions.append(claim_decision)
        pending.extend(claim_pending)
        blockers.extend(claim_blockers)
    decision["claim_decisions"] = claim_decisions
    decision["pending_confirmations"] = pending
    decision["blockers"] = blockers
    return decision


def build_writing_preparation_sheet(decision, view, claims):
    facts_and_judgments = {
        "confirmed": [],
        "requires_user_confirmation": [],
    }
    assumptions = {
        "confirmed": [],
        "requires_user_confirmation": [],
    }
    confirmed_information = [
        {
            "category": "task",
            "item_id": "task_mode",
            "value": decision["task_mode"],
            "basis": "user_input",
        },
        {
            "category": "material",
            "item_id": "material_view:{}".format(view["source_id"]),
            "value": {
                "material_status": view["material_status"],
                "is_formal_material": False,
            },
            "basis": "material_view_input",
        },
    ]
    pending_confirmations = list(decision["pending_confirmations"])
    confirmation_bases = {
        item_id: "decision_requires_user_confirmation"
        for item_id in pending_confirmations
    }
    claim_decisions = {
        item["claim_id"]: item
        for item in decision["claim_decisions"]
    }
    for claim in claims:
        claim_decision = claim_decisions[claim["claim_id"]]
        requires_confirmation = (
            claim_decision["action"]
            not in {"preserve", "preserve_source_force"}
        )
        item = {
            "claim_id": claim["claim_id"],
            "text": claim["text"],
            "evidence_status": claim["evidence_status"],
            "statement_force": claim_decision["allowed_statement_force"],
            "source_ref": claim["source_ref"],
        }
        if claim_decision["allowed_statement_force"] == "assumption":
            item["kind"] = "assumption"
        elif claim_decision["allowed_statement_force"] in {
            "professional_judgment",
            "recommended_solution",
        }:
            item["kind"] = "judgment"
        else:
            item["kind"] = "fact"
        bucket = (
            assumptions
            if claim_decision["allowed_statement_force"] == "assumption"
            else facts_and_judgments
        )
        status = (
            "requires_user_confirmation"
            if requires_confirmation
            else "confirmed"
        )
        bucket[status].append(item)
        confirmation_id = "claim:{}".format(claim["claim_id"])
        if requires_confirmation:
            if confirmation_id not in pending_confirmations:
                pending_confirmations.append(confirmation_id)
            confirmation_bases[confirmation_id] = (
                "claim_action:{}".format(claim_decision["action"])
            )
        else:
            confirmed_information.append(
                {
                    "category": "claim",
                    "item_id": confirmation_id,
                    "value": {
                        "kind": item["kind"],
                        "evidence_status": item["evidence_status"],
                        "statement_force": item["statement_force"],
                    },
                    "basis": item["source_ref"] or "user_input",
                }
            )

    material_review = decision["material_set_review"]
    material_inventory = [
        {
            "source_id": view["source_id"],
            "material_status": view["material_status"],
            "is_formal_material": False,
            "view_role": "derived_normalized_view",
        }
    ]
    if material_review["mode"] == "material_set":
        material_inventory.extend(material_review["materials"])
        for material in material_review["materials"]:
            confirmed_information.append(
                {
                    "category": "material",
                    "item_id": "material:{}".format(
                        material["material_id"]
                    ),
                    "value": {
                        "version": material["version"],
                        "material_subtype": material[
                            "material_subtype"
                        ],
                        "status": material["status"],
                    },
                    "basis": "material_set_input",
                }
            )
        for relationship in material_review["relationships"]:
            if relationship["relation_type"] in {
                "conflicts_with",
                "unclear",
            }:
                continue
            confirmed_information.append(
                {
                    "category": "relationship",
                    "item_id": "material_relation:{}".format(
                        relationship["relation_id"]
                    ),
                    "value": relationship["relation_type"],
                    "basis": relationship["basis"],
                }
            )
        for control_material in material_review["control_materials"]:
            confirmed_information.append(
                {
                    "category": "control_material",
                    "item_id": "control_material:{}".format(
                        control_material["material_id"]
                    ),
                    "value": control_material["material_id"],
                    "basis": control_material["control_bases"],
                }
            )

    for dimension in (
        "business_domain",
        "lifecycle_position",
        "document_scene",
        "material_subtype",
    ):
        classification_value = decision[dimension]
        if (
            classification_value["value"] != "unknown"
            and classification_value["confidence"] == "explicit"
        ):
            confirmed_information.append(
                {
                    "category": "perception",
                    "item_id": dimension,
                    "value": classification_value["value"],
                    "basis": "explicit_signal",
                }
            )

    claim_source_refs = []
    for claim in claims:
        source_ref = claim["source_ref"]
        if source_ref and source_ref not in claim_source_refs:
            claim_source_refs.append(source_ref)

    confirmation_categories = {
        "business_domain": "perception",
        "lifecycle_position": "perception",
        "document_scene": "perception",
        "material_subtype": "perception",
        "task_mode_support": "task",
    }
    requires_user_confirmation = []
    for item_id in pending_confirmations:
        prefix = item_id.split(":", 1)[0]
        if item_id in confirmation_categories:
            category = confirmation_categories[item_id]
        elif prefix in {
            "claim",
            "evidence",
            "evidence_force",
            "statement_force",
        }:
            category = "claim"
        elif prefix == "material_relation":
            category = "relationship"
        elif prefix == "material_conflict":
            category = "conflict"
        else:
            category = "material_set"
        requires_user_confirmation.append(
            {
                "category": category,
                "item_id": item_id,
                "basis": confirmation_bases[item_id],
            }
        )

    return {
        "schema_version": SCHEMA_VERSION,
        "current_stage": "preparation",
        "confirmation_required": True,
        "next_stage": "draft_after_user_confirmation",
        "material_inventory": material_inventory,
        "material_relationships": material_review["relationships"],
        "perception_dimensions": {
            "business_domain": decision["business_domain"],
            "lifecycle_position": decision["lifecycle_position"],
            "document_scene": decision["document_scene"],
            "material_subtype": decision["material_subtype"],
            "task_mode": decision["task_mode"],
        },
        "control_materials": material_review["control_materials"],
        "facts_and_judgments": facts_and_judgments,
        "assumptions": assumptions,
        "conflicts": material_review["conflicts"],
        "pending_confirmations": pending_confirmations,
        "confirmation_boundary": {
            "confirmed": confirmed_information,
            "requires_user_confirmation": requires_user_confirmation,
        },
        "traceability_summary": {
            "source_ids": [view["source_id"]]
            + [
                material["material_id"]
                for material in material_review.get("materials", [])
            ],
            "claim_source_refs": claim_source_refs,
            "relationship_ids": [
                relationship["relation_id"]
                for relationship in material_review["relationships"]
            ],
            "untraced_claim_ids": [
                claim["claim_id"]
                for claim in claims
                if not claim["source_ref"]
            ],
        },
        "proposed_contracts": list(decision["load_contracts"]),
        "blockers": list(decision["blockers"]),
    }


def build_explicit_domain_decision(task, route, business_domain):
    supports_bounded_task = task["mode"] in {
        "rewrite",
        "review",
        "annotation",
    }
    quick_task = supports_bounded_task and task["scope"] == "local"
    support_level = (
        "basic_support"
        if supports_bounded_task
        else "recognition_coverage"
    )
    return {
        "business_domain": classification(business_domain, "explicit"),
        "lifecycle_position": classification(
            route["lifecycle_position"], "explicit"
        ),
        "document_scene": classification(
            route["document_scene"], "explicit"
        ),
        "material_subtype": classification(
            route["material_subtype"], "explicit"
        ),
        "task_mode": task["mode"],
        "support_level": support_level,
        "processing_mode": "quick_path"
        if quick_task
        else "conservative_audit",
        "load_contracts": (
            CONTENT_CONTRACTS
            + [SCENE_CONTRACTS[route["document_scene"]]]
            + QUALITY_CONTRACTS
            if supports_bounded_task
            else list(COMMON_CONTRACTS)
        ),
        "pending_confirmations": (
            [] if supports_bounded_task else ["task_mode_support"]
        ),
        "blockers": [],
    }


def build_unclear_decision(task, text):
    allows_engineering_candidates = not has_active_research_context(text)
    has_research_marker = has_unnegated_research_marker(text)
    has_design_signal = allows_engineering_candidates and any(
        signal in text for signal in DESIGN_SIGNALS
    )
    has_engineering_acceptance_signal = (
        allows_engineering_candidates
        and "验收" in text
        and "工程" in text
    )
    has_ambiguous_project_acceptance_signal = (
        allows_engineering_candidates
        and "验收" in text
        and "项目" in text
    )
    has_generic_implementation_plan_signal = (
        allows_engineering_candidates
        and "实施方案" in text
        and "工程实施方案" not in text
    )
    has_generic_stage_report_signal = (
        allows_engineering_candidates
        and "阶段汇报" in text
        and not any(
            signal in text
            for signal in (
                "工程建设阶段汇报",
                "工程阶段汇报",
                "项目实施阶段汇报",
            )
        )
    )
    has_engineering_implementation_material_signal = (
        allows_engineering_candidates and "工程实施材料" in text
    )
    has_engineering_initiation_material_signal = (
        allows_engineering_candidates and "工程立项材料" in text
    )
    has_engineering_procurement_material_signal = (
        allows_engineering_candidates and "工程采购材料" in text
    )
    has_engineering_trial_run_material_signal = (
        allows_engineering_candidates and "工程试运行材料" in text
    )
    has_engineering_operation_material_signal = (
        allows_engineering_candidates
        and any(
            signal in text
            for signal in ("工程运营材料", "工程运行维护材料")
        )
    )
    has_research_application_material_signal = (
        has_research_marker and "申报" in text and "材料" in text
    )
    has_research_task_agreement_material_signal = (
        has_research_marker and "任务约定" in text and "材料" in text
    )
    has_research_implementation_material_signal = (
        has_research_marker
        and "研究实施" in text
        and "材料" in text
    )
    has_research_midterm_material_signal = (
        has_research_marker and "中期" in text
    )
    has_research_acceptance_material_signal = (
        has_research_marker and "验收" in text
    )
    has_cross_domain_engineering_plan_signal = (
        has_research_marker and "工程实施方案" in text
    )
    domain_candidates = []
    lifecycle_candidates = []
    scene_candidates = []
    material_subtype_candidates = []
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
        material_subtype_candidates.extend(
            [
                candidate(
                    "preliminary_design",
                    "设计信号不足以确认材料是否为初步设计。",
                ),
                candidate(
                    "detailed_design",
                    "设计信号不足以确认材料是否为详细设计。",
                ),
                candidate(
                    "overall_architecture",
                    "设计信号不足以确认材料是否为总体架构。",
                ),
            ]
        )
    if (
        has_engineering_acceptance_signal
        or has_ambiguous_project_acceptance_signal
    ):
        if has_ambiguous_project_acceptance_signal:
            domain_basis = (
                "项目验收信号不足以区分工程建设与科研课题语境。"
            )
        else:
            domain_basis = "材料出现工程验收信号，但未明确具体验收文种。"
        domain_candidates.append(
            candidate(
                "engineering_construction",
                domain_basis,
            )
        )
        lifecycle_candidates.append(
            candidate(
                "acceptance",
                "材料出现工程验收信号，但未明确验收活动位置。",
            )
        )
        scene_candidates.append(
            candidate(
                "review_acceptance",
                "材料可能适用评审验收场景，仍需确认具体文种。",
            )
        )
        if "验收大纲" in text:
            material_subtype_candidates.append(
                candidate(
                    "acceptance_outline",
                    "验收大纲名称已出现，但业务域仍待确认。",
                )
            )
        elif "验收报告" in text:
            material_subtype_candidates.append(
                candidate(
                    "acceptance_report",
                    "验收报告名称已出现，但业务域仍待确认。",
                )
            )
        else:
            material_subtype_candidates.extend(
                [
                    candidate(
                        "acceptance_outline",
                        "验收信号不足以确认材料是否为验收大纲。",
                    ),
                    candidate(
                        "acceptance_report",
                        "验收信号不足以确认材料是否为验收报告。",
                    ),
                ]
            )
    if has_generic_implementation_plan_signal:
        domain_candidates.extend(
            [
                candidate(
                    "engineering_construction",
                    "实施方案可能属于工程建设，但业务域尚未确认。",
                ),
                candidate(
                    "research_project",
                    "实施方案也可能属于科研课题，需确认研究任务语境。",
                ),
            ]
        )
        lifecycle_candidates.extend(
            [
                candidate(
                    "implementation",
                    "实施方案可能处于工程实施位置，仍需确认业务域。",
                ),
                candidate(
                    "research_implementation",
                    "实施方案可能处于科研研究实施位置，仍需确认业务域。",
                ),
            ]
        )
        scene_candidates.append(
            candidate(
                "architecture_design",
                "实施方案可能适用架构设计基础场景，仍需确认材料身份。",
            )
        )
        material_subtype_candidates.extend(
            [
                candidate(
                    "engineering_implementation_plan",
                    "泛称实施方案不足以确认其为工程实施方案。",
                ),
                candidate(
                    "research_implementation_plan",
                    "泛称实施方案不足以确认其为科研研究实施方案。",
                ),
            ]
        )
    if has_generic_stage_report_signal:
        domain_candidates.append(
            candidate(
                "engineering_construction",
                "阶段汇报可能属于工程建设，但也需排除科研或治理语境。",
            )
        )
        lifecycle_candidates.append(
            candidate(
                "implementation",
                "阶段汇报可能记录工程实施进展，仍需确认具体位置。",
            )
        )
        scene_candidates.append(
            candidate(
                "presentation",
                "阶段汇报具有汇报文种信号，但业务域仍待确认。",
            )
        )
        material_subtype_candidates.append(
            candidate(
                "stage_report",
                "泛称阶段汇报不足以确认其为工程建设阶段汇报。",
            )
        )
    if has_research_application_material_signal:
        domain_candidates.append(
            candidate(
                "research_project",
                "材料出现科研课题申报信号，但未明确是申报书还是可研论证材料。",
            )
        )
        lifecycle_candidates.append(
            candidate(
                "application",
                "科研课题申报信号支持申报生命周期候选。",
            )
        )
        scene_candidates.append(
            candidate(
                "feasibility_study",
                "科研申报材料可能适用可研立项基础场景。",
            )
        )
        material_subtype_candidates.extend(
            [
                candidate(
                    "research_application",
                    "科研申报材料可能是课题申报书。",
                ),
                candidate(
                    "research_feasibility_assessment",
                    "科研申报材料可能是可研论证材料。",
                ),
            ]
        )
    if has_research_task_agreement_material_signal:
        domain_candidates.append(
            candidate(
                "research_project",
                "材料出现科研课题任务约定信号，但未明确具体文种。",
            )
        )
        lifecycle_candidates.append(
            candidate(
                "task_agreement",
                "科研课题任务约定信号支持任务约定生命周期候选。",
            )
        )
        scene_candidates.append(
            candidate(
                "technical_spec",
                "科研任务约定材料可能适用技术规范基础场景。",
            )
        )
        material_subtype_candidates.append(
            candidate(
                "research_task_agreement",
                "科研任务约定材料可能是科研课题任务书。",
            )
        )
    if has_research_implementation_material_signal:
        domain_candidates.append(
            candidate(
                "research_project",
                "材料出现科研课题研究实施信号，但未明确具体文种。",
            )
        )
        lifecycle_candidates.append(
            candidate(
                "research_implementation",
                "科研课题研究实施信号支持研究实施生命周期候选。",
            )
        )
        scene_candidates.append(
            candidate(
                "architecture_design",
                "科研研究实施材料可能适用架构设计基础场景。",
            )
        )
        material_subtype_candidates.append(
            candidate(
                "research_implementation_plan",
                "科研研究实施材料可能是研究实施方案。",
            )
        )
    if has_research_midterm_material_signal:
        domain_candidates.append(
            candidate(
                "research_project",
                "材料出现科研课题中期信号，但未明确是汇报还是检查材料。",
            )
        )
        lifecycle_candidates.append(
            candidate(
                "midterm_review",
                "科研课题中期信号支持中期检查生命周期候选。",
            )
        )
        scene_candidates.extend(
            [
                candidate(
                    "presentation",
                    "科研中期材料可能是中期汇报。",
                ),
                candidate(
                    "review_acceptance",
                    "科研中期材料可能是中期检查材料。",
                ),
            ]
        )
        material_subtype_candidates.extend(
            [
                candidate(
                    "research_interim_report",
                    "科研中期材料可能是中期汇报。",
                ),
                candidate(
                    "research_interim_inspection",
                    "科研中期材料可能是中期检查材料。",
                ),
            ]
        )
    if has_research_acceptance_material_signal:
        domain_candidates.append(
            candidate(
                "research_project",
                "材料出现科研课题验收信号，但未明确是否为结题验收材料。",
            )
        )
        lifecycle_candidates.append(
            candidate(
                "final_acceptance",
                "科研课题验收信号支持结题验收生命周期候选。",
            )
        )
        scene_candidates.append(
            candidate(
                "review_acceptance",
                "科研课题验收材料可能适用评审验收基础场景。",
            )
        )
        material_subtype_candidates.append(
            candidate(
                "research_final_acceptance",
                "科研课题验收报告不足以确认其为结题验收材料。",
            )
        )
    if has_cross_domain_engineering_plan_signal:
        domain_candidates.extend(
            [
                candidate(
                    "engineering_construction",
                    "标题给出工程实施方案，但科研课题归属信号与其冲突。",
                ),
                candidate(
                    "research_project",
                    "任务给出科研课题归属，但标题仍为工程实施方案。",
                ),
            ]
        )
        lifecycle_candidates.extend(
            [
                candidate(
                    "implementation",
                    "工程实施方案标题支持工程实施位置候选。",
                ),
                candidate(
                    "research_implementation",
                    "科研课题归属支持研究实施位置候选。",
                ),
            ]
        )
        scene_candidates.append(
            candidate(
                "architecture_design",
                "两类实施方案均可能加载架构设计基础场景。",
            )
        )
        material_subtype_candidates.extend(
            [
                candidate(
                    "engineering_implementation_plan",
                    "标题明确给出工程实施方案。",
                ),
                candidate(
                    "research_implementation_plan",
                    "科研课题归属与实施方案信号形成科研候选。",
                ),
            ]
        )
    if has_engineering_implementation_material_signal:
        domain_candidates.append(
            candidate(
                "engineering_construction",
                "材料明确处于工程实施语境，但未说明具体文种。",
            )
        )
        lifecycle_candidates.append(
            candidate(
                "implementation",
                "工程实施信号支持实施位置候选，具体材料仍待确认。",
            )
        )
        scene_candidates.extend(
            [
                candidate(
                    "architecture_design",
                    "工程实施材料可能是实施方案。",
                ),
                candidate(
                    "review_acceptance",
                    "工程实施材料可能是实施记录。",
                ),
            ]
        )
        material_subtype_candidates.extend(
            [
                candidate(
                    "engineering_implementation_plan",
                    "工程实施材料可能是实施方案。",
                ),
                candidate(
                    "implementation_record",
                    "工程实施材料可能是实施记录。",
                ),
            ]
        )
    if has_engineering_initiation_material_signal:
        domain_candidates.append(
            candidate(
                "engineering_construction",
                "材料明确处于工程立项语境，但未说明具体文种。",
            )
        )
        lifecycle_candidates.append(
            candidate(
                "initiation",
                "工程立项信号支持立项位置候选，具体材料仍待确认。",
            )
        )
        scene_candidates.append(
            candidate(
                "feasibility_study",
                "工程立项材料可能是项目建议书或可行性研究报告。",
            )
        )
        material_subtype_candidates.extend(
            [
                candidate(
                    "project_proposal",
                    "工程立项材料可能是项目建议书。",
                ),
                candidate(
                    "feasibility_study",
                    "工程立项材料可能是可行性研究报告。",
                ),
            ]
        )
    if has_engineering_procurement_material_signal:
        domain_candidates.append(
            candidate(
                "engineering_construction",
                "材料明确处于工程采购语境，但未说明具体文种。",
            )
        )
        lifecycle_candidates.append(
            candidate(
                "procurement",
                "工程采购信号支持采购位置候选，具体材料仍待确认。",
            )
        )
        scene_candidates.extend(
            [
                candidate(
                    "technical_spec",
                    "工程采购材料可能是技术规范书。",
                ),
                candidate(
                    "bid_response",
                    "工程采购材料可能是投标技术应答。",
                ),
            ]
        )
        material_subtype_candidates.extend(
            [
                candidate(
                    "technical_specification",
                    "工程采购材料可能是技术规范书。",
                ),
                candidate(
                    "bid_response",
                    "工程采购材料可能是投标技术应答。",
                ),
            ]
        )
    if has_engineering_trial_run_material_signal:
        domain_candidates.append(
            candidate(
                "engineering_construction",
                "材料明确处于工程试运行语境，但未说明具体文种。",
            )
        )
        lifecycle_candidates.append(
            candidate(
                "trial_run",
                "工程试运行信号支持试运行位置候选。",
            )
        )
        scene_candidates.append(
            candidate(
                "review_acceptance",
                "工程试运行材料可能是试运行报告。",
            )
        )
        material_subtype_candidates.append(
            candidate(
                "trial_run_report",
                "工程试运行材料可能是试运行报告。",
            )
        )
    if has_engineering_operation_material_signal:
        domain_candidates.append(
            candidate(
                "engineering_construction",
                "材料明确处于工程运营语境，但未说明具体文种。",
            )
        )
        lifecycle_candidates.append(
            candidate(
                "operation",
                "工程运营信号支持运营位置候选。",
            )
        )
        scene_candidates.append(
            candidate(
                "presentation",
                "工程运营材料可能是运行维护或运营报告。",
            )
        )
        material_subtype_candidates.append(
            candidate(
                "operation_report",
                "工程运营材料可能是运行维护或运营报告。",
            )
        )

    material_subtype_candidates = [
        item
        for item in material_subtype_candidates
        if not is_material_subtype_negated(
            task["instruction"], item["value"]
        )
    ]

    pending = [
        "business_domain",
        "lifecycle_position",
        "document_scene",
        "material_subtype",
    ]
    return {
        "business_domain": classification(
            "unknown", "unclear", unique_candidates(domain_candidates)
        ),
        "lifecycle_position": classification(
            "unknown", "unclear", unique_candidates(lifecycle_candidates)
        ),
        "document_scene": classification(
            "unknown", "unclear", unique_candidates(scene_candidates)
        ),
        "material_subtype": classification(
            "unknown",
            "unclear",
            unique_candidates(material_subtype_candidates),
        ),
        "task_mode": task["mode"],
        "support_level": "recognition_coverage",
        "processing_mode": "conservative_audit",
        "load_contracts": list(COMMON_CONTRACTS),
        "pending_confirmations": pending,
        "blockers": [],
    }


def build_perception_decision(request):
    """Return the observable decision for one task and normalized view."""
    request = require_mapping(request, "request")
    task = validate_task(request.get("task"))
    view = validate_material_view(request.get("material_view"))
    claims = validate_claims(request.get("claims"))
    material_set = validate_material_set(request.get("material_set"))
    text = "\n".join(
        [task["instruction"], view["title"], view["searchable_text"]]
    )

    research_title_routes = matching_research_routes(view["title"])
    engineering_title_routes = matching_engineering_routes(view["title"])
    research_routes = resolve_research_identity_routes(task, view)
    matching_routes = resolve_engineering_identity_routes(task, view)
    if len(research_title_routes) == 1 and len(research_routes) == 1:
        decision = build_explicit_domain_decision(
            task, research_routes[0], "research_project"
        )
    elif len(engineering_title_routes) == 1 and len(matching_routes) == 1:
        decision = build_explicit_domain_decision(
            task, matching_routes[0], "engineering_construction"
        )
    elif len(research_routes) == 1:
        decision = build_explicit_domain_decision(
            task, research_routes[0], "research_project"
        )
    elif len(matching_routes) == 1:
        decision = build_explicit_domain_decision(
            task, matching_routes[0], "engineering_construction"
        )
    else:
        decision = build_unclear_decision(task, text)
    decision = apply_claim_boundaries(decision, claims)
    if (
        decision["processing_mode"] == "quick_path"
        and (
            decision["pending_confirmations"]
            or decision["blockers"]
        )
    ):
        decision["processing_mode"] = "conservative_audit"
    if material_set is not None:
        decision["processing_mode"] = "conservative_audit"
        decision["load_contracts"] = decision["load_contracts"] + [
            "common.material_set_review"
        ]
        review, material_pending, material_blockers = (
            build_material_set_review(material_set)
        )
        decision["material_set_review"] = review
        decision["pending_confirmations"].extend(material_pending)
        decision["blockers"].extend(material_blockers)
    else:
        decision["material_set_review"] = build_single_material_review()
    complete_plan_creation = (
        task["mode"] == "create"
        and task["scope"] == "document"
        and decision["business_domain"]["value"]
        in {"engineering_construction", "research_project"}
        and decision["material_subtype"]["value"] != "unknown"
    )
    if complete_plan_creation or material_set is not None:
        decision["processing_mode"] = "two_stage"
        decision["load_contracts"].append(
            "common.writing_preparation"
        )
        decision["writing_preparation_sheet"] = (
            build_writing_preparation_sheet(decision, view, claims)
        )

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
