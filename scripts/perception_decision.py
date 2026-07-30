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
    "common.statement_force_policy",
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
    claims = validate_claims(request.get("claims"))
    material_set = validate_material_set(request.get("material_set"))
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
    decision = apply_claim_boundaries(decision, claims)
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
