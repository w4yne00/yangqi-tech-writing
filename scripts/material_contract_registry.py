#!/usr/bin/env python3
"""Validate material-contract definitions and their sample evidence registry."""

import argparse
from collections import Counter
import json
from pathlib import Path
import sys

from project_context import find_sensitive_paths


SCHEMA_VERSION = "1.0"
ARTIFACT_TYPE = "material_contract_evidence_bundle"

SUPPORT_LEVELS = {
    "recognition_coverage",
    "basic_support",
    "deep_support",
    "joint_review_support",
    "forward_validation",
}
SOURCE_TYPES = {"formal_requirement", "real_case", "synthetic_case"}
AUTHORIZATION_STATUSES = {
    "authorized",
    "public_reuse",
    "restricted",
    "unknown",
}
REDACTION_STATUSES = {"redacted", "not_required", "pending", "failed"}
REVIEW_STATUSES = {"approved", "pending", "rejected"}
CASE_TYPES = {
    "formal_requirement",
    "positive",
    "failure",
    "lifecycle_boundary",
    "missing_information",
    "traceability_gap",
    "version_conflict",
    "statement_force_unclear",
    "explicit_supersession",
    "forward_validation",
}
DATA_CLASSIFICATIONS = {
    "public",
    "deidentified_reusable",
    "project_restricted",
    "prohibited_persistence",
}
INTENDED_USES = {
    "private_review",
    "generic_rule",
    "public_eval",
    "capability_evidence",
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

ROOT_FIELDS = {"schema_version", "artifact_type", "contract", "samples"}
CONTRACT_FIELDS = {
    "contract_id",
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
}
IDENTITY_FIELDS = {
    "business_domain",
    "lifecycle_position",
    "document_scene",
    "material_subtype",
}
SAMPLE_FIELDS = {
    "sample_id",
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
}
SOURCE_FIELDS = {"source_id", "source_type", "locator"}
AUTHORIZATION_FIELDS = {"status", "scope"}
TRANSITION_FIELDS = {"from", "to"}

DEEP_SUPPORT_CASES = {
    "formal_requirement",
    "positive",
    "failure",
    "lifecycle_boundary",
    "missing_information",
}
JOINT_REVIEW_CASES = DEEP_SUPPORT_CASES | {
    "traceability_gap",
    "version_conflict",
    "statement_force_unclear",
    "explicit_supersession",
}


class ContractError(ValueError):
    """A safe public validation error."""

    def __init__(self, message, code="invalid_bundle"):
        super().__init__(message)
        self.code = code


def require_mapping(value, field):
    if not isinstance(value, dict):
        raise ContractError("{} 必须是对象".format(field))
    return value


def reject_unknown_fields(mapping, allowed, field):
    unknown = sorted(set(mapping) - set(allowed))
    if unknown:
        raise ContractError(
            "{}.unknown_fields: {}".format(field, ", ".join(unknown))
        )


def require_fields(mapping, required, field, code="invalid_bundle"):
    missing = sorted(set(required) - set(mapping))
    if missing:
        raise ContractError(
            "{}.missing_fields: {}".format(field, ", ".join(missing)),
            code,
        )


def require_text(mapping, field, prefix):
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ContractError("{}.{} 必须是非空字符串".format(prefix, field))
    return value.strip()


def require_text_list(value, field):
    if not isinstance(value, list) or not value:
        raise ContractError("{} 必须是非空数组".format(field))
    result = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ContractError(
                "{}[{}] 必须是非空字符串".format(field, index)
            )
        normalized = item.strip()
        if normalized in result:
            raise ContractError(
                "{} 不得包含重复值: {}".format(field, normalized)
            )
        result.append(normalized)
    return result


def validate_named_entries(raw_entries, field, required_fields):
    if not isinstance(raw_entries, list) or not raw_entries:
        raise ContractError("{} 必须是非空数组".format(field))
    normalized = []
    for index, raw_entry in enumerate(raw_entries):
        entry_field = "{}[{}]".format(field, index)
        entry = require_mapping(raw_entry, entry_field)
        reject_unknown_fields(entry, required_fields, entry_field)
        require_fields(
            entry,
            required_fields,
            entry_field,
            "missing_contract_metadata",
        )
        normalized.append(
            {
                name: (
                    entry[name]
                    if name == "required"
                    else require_text(entry, name, entry_field)
                )
                for name in sorted(required_fields)
            }
        )
        if "required" in required_fields and not isinstance(
            entry.get("required"), bool
        ):
            raise ContractError(
                "{}.required 必须是布尔值".format(entry_field)
            )
    return normalized


def validate_statement_transitions(raw_transitions):
    field = "contract.statement_force.prohibited_transitions"
    if not isinstance(raw_transitions, list) or not raw_transitions:
        raise ContractError("{} 必须是非空数组".format(field))
    transitions = []
    seen = set()
    for index, raw_transition in enumerate(raw_transitions):
        item_field = "{}[{}]".format(field, index)
        transition = require_mapping(raw_transition, item_field)
        reject_unknown_fields(transition, TRANSITION_FIELDS, item_field)
        require_fields(
            transition,
            TRANSITION_FIELDS,
            item_field,
            "missing_contract_metadata",
        )
        from_force = require_text(transition, "from", item_field)
        to_force = require_text(transition, "to", item_field)
        unknown_forces = sorted(
            {from_force, to_force} - STATEMENT_FORCES
        )
        if unknown_forces:
            raise ContractError(
                "{} 包含不受支持的陈述效力: {}".format(
                    item_field, ", ".join(unknown_forces)
                )
            )
        key = (from_force, to_force)
        if key in seen:
            raise ContractError(
                "{} 不得包含重复跃迁: {} -> {}".format(
                    field, from_force, to_force
                )
            )
        seen.add(key)
        transitions.append({"from": from_force, "to": to_force})
    return transitions


def validate_contract(raw_contract):
    contract = require_mapping(raw_contract, "contract")
    reject_unknown_fields(contract, CONTRACT_FIELDS, "contract")
    require_fields(
        contract,
        CONTRACT_FIELDS,
        "contract",
        "missing_contract_metadata",
    )

    identity = require_mapping(
        contract.get("applicable_identity"), "contract.applicable_identity"
    )
    reject_unknown_fields(
        identity, IDENTITY_FIELDS, "contract.applicable_identity"
    )
    require_fields(
        identity,
        IDENTITY_FIELDS,
        "contract.applicable_identity",
        "missing_contract_metadata",
    )
    normalized_identity = {
        field: require_text(
            identity, field, "contract.applicable_identity"
        )
        for field in sorted(IDENTITY_FIELDS)
    }

    required_inputs = validate_named_entries(
        contract.get("required_inputs"),
        "contract.required_inputs",
        {"input_id", "description", "required"},
    )
    content_responsibilities = validate_named_entries(
        contract.get("content_responsibilities"),
        "contract.content_responsibilities",
        {"responsibility_id", "description"},
    )
    reasonable_depth = validate_named_entries(
        contract.get("reasonable_depth"),
        "contract.reasonable_depth",
        {"depth_id", "description"},
    )

    statement_force = require_mapping(
        contract.get("statement_force"), "contract.statement_force"
    )
    reject_unknown_fields(
        statement_force,
        {"allowed", "prohibited_transitions"},
        "contract.statement_force",
    )
    require_fields(
        statement_force,
        {"allowed", "prohibited_transitions"},
        "contract.statement_force",
        "missing_contract_metadata",
    )
    allowed_forces = require_text_list(
        statement_force.get("allowed"), "contract.statement_force.allowed"
    )
    unknown_forces = sorted(set(allowed_forces) - STATEMENT_FORCES)
    if unknown_forces:
        raise ContractError(
            (
                "contract.statement_force.allowed "
                "包含不受支持的陈述效力: {}"
            ).format(", ".join(unknown_forces))
        )
    prohibited_transitions = validate_statement_transitions(
        statement_force.get("prohibited_transitions")
    )

    traceability = validate_named_entries(
        contract.get("traceability"),
        "contract.traceability",
        {"trace_id", "description"},
    )
    common_failures = validate_named_entries(
        contract.get("common_failures"),
        "contract.common_failures",
        {"failure_id", "description"},
    )
    missing_information_handling = validate_named_entries(
        contract.get("missing_information_handling"),
        "contract.missing_information_handling",
        {"missing_id", "action"},
    )
    validation_case_ids = require_text_list(
        contract.get("validation_case_ids"),
        "contract.validation_case_ids",
    )
    support_level = require_text(contract, "support_level", "contract")
    if support_level not in SUPPORT_LEVELS:
        raise ContractError("contract.support_level 不是受支持的支持级别")

    return {
        "contract_id": require_text(contract, "contract_id", "contract"),
        "applicable_identity": normalized_identity,
        "required_inputs": required_inputs,
        "content_responsibilities": content_responsibilities,
        "reasonable_depth": reasonable_depth,
        "statement_force": {
            "allowed": allowed_forces,
            "prohibited_transitions": prohibited_transitions,
        },
        "traceability": traceability,
        "common_failures": common_failures,
        "missing_information_handling": missing_information_handling,
        "validation_case_ids": validation_case_ids,
        "support_level": support_level,
    }


def validate_samples(raw_samples):
    if not isinstance(raw_samples, list):
        raise ContractError("samples 必须是数组")
    samples = []
    seen = set()
    for index, raw_sample in enumerate(raw_samples):
        field = "samples[{}]".format(index)
        sample = require_mapping(raw_sample, field)
        reject_unknown_fields(sample, SAMPLE_FIELDS, field)
        require_fields(
            sample, SAMPLE_FIELDS, field, "missing_sample_metadata"
        )
        sample_id = require_text(sample, "sample_id", field)
        if sample_id in seen:
            raise ContractError("samples.sample_id 不得重复: {}".format(sample_id))
        seen.add(sample_id)

        source = require_mapping(sample.get("source"), "{}.source".format(field))
        reject_unknown_fields(source, SOURCE_FIELDS, "{}.source".format(field))
        require_fields(
            source,
            SOURCE_FIELDS,
            "{}.source".format(field),
            "missing_sample_metadata",
        )
        source_type = require_text(source, "source_type", "{}.source".format(field))
        if source_type not in SOURCE_TYPES:
            raise ContractError("{}.source.source_type 不受支持".format(field))

        authorization = require_mapping(
            sample.get("authorization"), "{}.authorization".format(field)
        )
        reject_unknown_fields(
            authorization,
            AUTHORIZATION_FIELDS,
            "{}.authorization".format(field),
        )
        require_fields(
            authorization,
            AUTHORIZATION_FIELDS,
            "{}.authorization".format(field),
            "missing_sample_metadata",
        )
        authorization_status = require_text(
            authorization, "status", "{}.authorization".format(field)
        )
        if authorization_status not in AUTHORIZATION_STATUSES:
            raise ContractError(
                "{}.authorization.status 不受支持".format(field)
            )
        authorization_scope = require_text_list(
            authorization.get("scope"),
            "{}.authorization.scope".format(field),
        )
        unknown_scope_uses = sorted(
            set(authorization_scope) - INTENDED_USES
        )
        if unknown_scope_uses:
            raise ContractError(
                "{}.authorization.scope 包含不受支持的用途: {}".format(
                    field, ", ".join(unknown_scope_uses)
                )
            )

        redaction_status = require_text(sample, "redaction_status", field)
        if redaction_status not in REDACTION_STATUSES:
            raise ContractError("{}.redaction_status 不受支持".format(field))
        review_status = require_text(sample, "review_status", field)
        if review_status not in REVIEW_STATUSES:
            raise ContractError("{}.review_status 不受支持".format(field))
        case_type = require_text(sample, "case_type", field)
        if case_type not in CASE_TYPES:
            raise ContractError("{}.case_type 不受支持".format(field))
        data_classification = require_text(
            sample, "data_classification", field
        )
        if data_classification not in DATA_CLASSIFICATIONS:
            raise ContractError(
                "{}.data_classification 不受支持".format(field)
            )
        if data_classification == "prohibited_persistence":
            raise ContractError(
                "样本 {} 被标记为禁止持久化信息，登记已阻断".format(
                    sample_id
                ),
                "persistence_rejected_sensitive_data",
            )
        intended_uses = require_text_list(
            sample.get("intended_uses"), "{}.intended_uses".format(field)
        )
        unknown_uses = sorted(set(intended_uses) - INTENDED_USES)
        if unknown_uses:
            raise ContractError(
                "{}.intended_uses 包含不受支持的用途: {}".format(
                    field, ", ".join(unknown_uses)
                )
            )
        reusable_uses = {
            "generic_rule",
            "public_eval",
            "capability_evidence",
        }
        unauthorized_uses = sorted(
            set(intended_uses) - set(authorization_scope)
        )
        if unauthorized_uses:
            raise ContractError(
                "样本 {} 的用途超出授权范围: {}".format(
                    sample_id, ", ".join(unauthorized_uses)
                ),
                "authorization_scope_violation",
            )
        if (
            authorization_status not in {"authorized", "public_reuse"}
            and reusable_uses.intersection(intended_uses)
        ):
            raise ContractError(
                (
                    "样本 {} 未获得可复用授权，不能进入通用规则、"
                    "公开评测或能力证据"
                ).format(sample_id),
                "authorization_scope_violation",
            )
        if (
            review_status != "approved"
            and reusable_uses.intersection(intended_uses)
        ):
            raise ContractError(
                (
                    "样本 {} 尚未通过评审，不能进入通用规则、"
                    "公开评测或能力证据"
                ).format(sample_id),
                "review_status_violation",
            )
        if (
            data_classification == "project_restricted"
            and reusable_uses.intersection(intended_uses)
        ):
            raise ContractError(
                (
                    "项目受限样本 {} 只能登记为 private_review，"
                    "不能进入通用规则、公开评测或能力证据"
                ).format(sample_id),
                "project_restricted_scope_violation",
            )
        if (
            source_type == "real_case"
            and redaction_status != "redacted"
            and reusable_uses.intersection(intended_uses)
        ):
            raise ContractError(
                (
                    "真实样本 {} 未完成脱敏，不能进入通用规则、"
                    "公开评测或能力证据"
                ).format(sample_id),
                "unredacted_sample",
            )
        evidence_type = require_text(sample, "evidence_type", field)
        model_execution = sample.get("model_execution")
        if not isinstance(model_execution, bool):
            raise ContractError("{}.model_execution 必须是布尔值".format(field))
        if (
            source_type == "synthetic_case"
            and evidence_type != "deterministic-synthetic-fixture"
        ):
            raise ContractError(
                (
                    "合成样本 {} 的 evidence_type 必须为 "
                    "deterministic-synthetic-fixture，并明确记录 "
                    "model_execution"
                ).format(sample_id),
                "invalid_synthetic_evidence_metadata",
            )
        if source_type == "formal_requirement" and (
            case_type != "formal_requirement"
            or evidence_type != "formal-requirement"
        ):
            raise ContractError(
                (
                    "正式要求样本 {} 必须使用 formal_requirement "
                    "案例类型和 formal-requirement 证据类型"
                ).format(sample_id),
                "invalid_evidence_metadata",
            )
        if source_type == "real_case" and (
            case_type == "formal_requirement"
            or evidence_type != "deidentified-real-case"
        ):
            raise ContractError(
                (
                    "真实案例样本 {} 不能替代 formal_requirement，且 "
                    "evidence_type 必须为 deidentified-real-case"
                ).format(sample_id),
                "invalid_evidence_metadata",
            )

        samples.append(
            {
                "sample_id": sample_id,
                "source": {
                    "source_id": require_text(
                        source, "source_id", "{}.source".format(field)
                    ),
                    "source_type": source_type,
                    "locator": require_text(
                        source, "locator", "{}.source".format(field)
                    ),
                },
                "authorization": {
                    "status": authorization_status,
                    "scope": authorization_scope,
                },
                "redaction_status": redaction_status,
                "material_version": require_text(
                    sample, "material_version", field
                ),
                "review_status": review_status,
                "case_type": case_type,
                "data_classification": data_classification,
                "intended_uses": intended_uses,
                "evidence_type": evidence_type,
                "model_execution": model_execution,
            }
        )
    return samples


def is_capability_evidence(sample, validation_case_ids):
    if sample["sample_id"] not in validation_case_ids:
        return False
    if "capability_evidence" not in sample["intended_uses"]:
        return False
    if sample["authorization"]["status"] not in {
        "authorized",
        "public_reuse",
    }:
        return False
    if sample["review_status"] != "approved":
        return False
    if sample["data_classification"] not in {
        "public",
        "deidentified_reusable",
    }:
        return False
    if (
        sample["case_type"] == "forward_validation"
        and sample["model_execution"] is not True
    ):
        return False
    if sample["source"]["source_type"] == "formal_requirement":
        return (
            sample["case_type"] == "formal_requirement"
            and sample["redaction_status"] in {"redacted", "not_required"}
            and sample["evidence_type"] == "formal-requirement"
        )
    if sample["source"]["source_type"] == "real_case":
        return (
            sample["redaction_status"] == "redacted"
            and sample["evidence_type"] == "deidentified-real-case"
        )
    return False


def validate_support_claim(contract, eligible_samples):
    support_level = contract["support_level"]
    eligible_case_types = {sample["case_type"] for sample in eligible_samples}
    if support_level == "deep_support":
        missing = sorted(DEEP_SUPPORT_CASES - eligible_case_types)
    elif support_level in {"joint_review_support", "forward_validation"}:
        required = JOINT_REVIEW_CASES
        if support_level == "forward_validation":
            required = required | {"forward_validation"}
        missing = sorted(required - eligible_case_types)
    else:
        missing = []
    if missing:
        raise ContractError(
            "{} 缺少可计入能力声明的正式要求或真实案例: {}".format(
                support_level, ", ".join(missing)
            ),
            "unsupported_capability_claim",
        )


def validate_bundle(raw_bundle):
    bundle = require_mapping(raw_bundle, "bundle")
    sensitive_paths = find_sensitive_paths(bundle)
    if sensitive_paths:
        raise ContractError(
            "检测到禁止持久化信息；请移除后重试（paths: {}）".format(
                ", ".join(sensitive_paths)
            ),
            "persistence_rejected_sensitive_data",
        )
    reject_unknown_fields(bundle, ROOT_FIELDS, "bundle")
    if bundle.get("schema_version") != SCHEMA_VERSION:
        raise ContractError("bundle.schema_version 必须为 {}".format(SCHEMA_VERSION))
    if bundle.get("artifact_type") != ARTIFACT_TYPE:
        raise ContractError(
            "bundle.artifact_type 必须为 {}".format(ARTIFACT_TYPE)
        )

    contract = validate_contract(bundle.get("contract"))
    samples = validate_samples(bundle.get("samples"))
    sample_ids = {sample["sample_id"] for sample in samples}
    missing_sample_ids = sorted(set(contract["validation_case_ids"]) - sample_ids)
    if missing_sample_ids:
        raise ContractError(
            "contract.validation_case_ids 引用了不存在的样本: {}".format(
                ", ".join(missing_sample_ids)
            )
        )

    eligible_samples = [
        sample
        for sample in samples
        if is_capability_evidence(sample, contract["validation_case_ids"])
    ]
    validate_support_claim(contract, eligible_samples)
    eligible_ids = {sample["sample_id"] for sample in eligible_samples}
    excluded_sample_ids = [
        sample_id
        for sample_id in contract["validation_case_ids"]
        if sample_id not in eligible_ids
    ]
    counts = Counter(sample["case_type"] for sample in eligible_samples)

    return {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": ARTIFACT_TYPE,
        "validation": {"status": "valid"},
        "contract": {
            "contract_id": contract["contract_id"],
            "applicable_identity": contract["applicable_identity"],
            "support_level": contract["support_level"],
        },
        "evidence_summary": {
            "eligible_case_counts": dict(counts),
            "excluded_sample_ids": excluded_sample_ids,
        },
    }


def read_bundle(path):
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser(
        description="校验材料合同模板、样本元数据和能力支持级别。"
    )
    parser.add_argument(
        "bundle", help="登记包 JSON 文件；使用 - 从标准输入读取"
    )
    args = parser.parse_args()

    try:
        result = validate_bundle(read_bundle(args.bundle))
    except ContractError as exc:
        print(
            json.dumps(
                {"error": exc.code, "message": str(exc)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1
    except (OSError, json.JSONDecodeError) as exc:
        print(
            json.dumps(
                {"error": "invalid_bundle", "message": str(exc)},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        return 1

    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
