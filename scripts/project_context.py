#!/usr/bin/env python3
"""Maintain an optional, confirmed and project-isolated local context package."""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys
import tempfile


SCHEMA_VERSION = "1.0"
ARTIFACT_TYPE = "project_context_package"

REQUEST_FIELDS = {
    "schema_version",
    "project_id",
    "expected_revision",
    "confirmation",
    "update",
}
UPDATE_FIELDS = {
    "materials",
    "relationships",
    "scope",
    "terms",
    "facts",
    "assumptions",
    "decisions",
    "conclusions",
    "conflicts",
    "trace_links",
}
MATERIAL_FIELDS = {
    "material_id",
    "title",
    "version",
    "material_subtype",
    "status",
    "source_id",
    "content_digest",
}
RELATIONSHIP_FIELDS = {
    "relation_id",
    "from_material_id",
    "to_material_id",
    "relation_type",
    "basis",
    "source_material_ids",
}
RECORD_SPECS = {
    "scope": (
        "scope_id",
        {"scope_id", "text", "source_material_ids"},
        ("text",),
    ),
    "terms": (
        "term_id",
        {"term_id", "term", "definition", "source_material_ids"},
        ("term", "definition"),
    ),
    "facts": (
        "fact_id",
        {"fact_id", "text", "source_material_ids"},
        ("text",),
    ),
    "assumptions": (
        "assumption_id",
        {"assumption_id", "text", "source_material_ids"},
        ("text",),
    ),
    "decisions": (
        "decision_id",
        {"decision_id", "text", "source_material_ids"},
        ("text",),
    ),
    "conclusions": (
        "conclusion_id",
        {"conclusion_id", "text", "source_material_ids"},
        ("text",),
    ),
    "conflicts": (
        "conflict_id",
        {"conflict_id", "text", "source_material_ids"},
        ("text",),
    ),
    "trace_links": (
        "trace_id",
        {
            "trace_id",
            "from_ref",
            "to_ref",
            "relation_type",
            "source_material_ids",
        },
        ("from_ref", "to_ref", "relation_type"),
    ),
}
COLLECTION_TARGETS = {
    "relationships": "confirmed_relationships",
    "facts": "confirmed_facts",
    "materials": "materials",
    "scope": "scope",
    "terms": "terms",
    "assumptions": "assumptions",
    "decisions": "decisions",
    "conclusions": "conclusions",
    "conflicts": "conflicts",
    "trace_links": "trace_links",
}
PACKAGE_COLLECTIONS = tuple(COLLECTION_TARGETS.values())

MATERIAL_STATUSES = {
    "draft",
    "approved",
    "signed",
    "effective",
    "superseded",
    "unknown",
}
RELATION_TYPES = {
    "governs",
    "derives_from",
    "supersedes",
    "implements",
    "verifies",
    "conflicts_with",
    "unclear",
}

SENSITIVE_FIELD = re.compile(
    r"^(?:password|passwd|passphrase|secret|token|api[_-]?key|"
    r"access[_-]?key|private[_-]?key|credential|username|login|account|"
    r"personal(?:_info)?|person_name|contact|email|phone|mobile|id_card|"
    r"口令|密码|密钥|令牌|账号|用户名|姓名|联系方式|邮箱|手机号|身份证)$",
    re.IGNORECASE,
)
SENSITIVE_VALUES = (
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
    re.compile(r"\b(?:gh[opusr]_[A-Za-z0-9]{20,}|xox[baprs]-[A-Za-z0-9-]{10,})\b"),
    re.compile(r"\bAKIA[A-Z0-9]{16}\b"),
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{12,}", re.IGNORECASE),
    re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE),
    re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)"),
    re.compile(r"(?:真实)?(?:账号|用户名)\s*(?:为|是|[:：=])\s*\S+"),
    re.compile(
        r"\b(?:password|passwd|passphrase|secret|token)\b"
        r"\s*(?:is|[:=：])\s*\S+|"
        r"\b(?:access|api)[ _-]+key\b"
        r"\s*(?:is|[:=：])\s*\S+|"
        r"(?:访问)?(?:口令|密码|密钥|令牌)"
        r"\s*(?:为|是|[:=：])\s*\S+",
        re.IGNORECASE,
    ),
)


class ContextError(ValueError):
    """A safe public error that does not contain rejected field values."""

    def __init__(self, message, code="invalid_request"):
        super().__init__(message)
        self.code = code


def require_mapping(value, field):
    if not isinstance(value, dict):
        raise ContextError("{} 必须是对象".format(field))
    return value


def require_text(mapping, field, prefix=""):
    value = mapping.get(field)
    if not isinstance(value, str) or not value.strip():
        label = "{}.{}".format(prefix, field) if prefix else field
        raise ContextError("{} 必须是非空字符串".format(label))
    return value.strip()


def reject_unknown_fields(mapping, allowed, field):
    unknown = sorted(set(mapping) - set(allowed))
    if unknown:
        raise ContextError(
            "{}.unknown_fields: {}".format(field, ", ".join(unknown))
        )


def find_sensitive_paths(value, path="$"):
    findings = []
    if isinstance(value, dict):
        for key, child in value.items():
            child_path = "{}.{}".format(path, key)
            if isinstance(key, str) and SENSITIVE_FIELD.fullmatch(key):
                findings.append(child_path)
            findings.extend(find_sensitive_paths(child, child_path))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            findings.extend(
                find_sensitive_paths(child, "{}[{}]".format(path, index))
            )
    elif isinstance(value, str):
        if any(pattern.search(value) for pattern in SENSITIVE_VALUES):
            findings.append(path)
    return sorted(set(findings))


def require_source_material_ids(record, field):
    raw_ids = record.get("source_material_ids", [])
    if not isinstance(raw_ids, list):
        raise ContextError("{}.source_material_ids 必须是数组".format(field))
    source_ids = []
    for index, value in enumerate(raw_ids):
        if not isinstance(value, str) or not value.strip():
            raise ContextError(
                "{}.source_material_ids[{}] 必须是非空字符串".format(
                    field, index
                )
            )
        normalized = value.strip()
        if normalized not in source_ids:
            source_ids.append(normalized)
    return source_ids


def validate_materials(raw_materials):
    if not isinstance(raw_materials, list):
        raise ContextError("update.materials 必须是数组")
    materials = []
    seen = set()
    for index, raw_material in enumerate(raw_materials):
        field = "update.materials[{}]".format(index)
        material = require_mapping(raw_material, field)
        reject_unknown_fields(material, MATERIAL_FIELDS, field)
        material_id = require_text(material, "material_id", field)
        if material_id in seen:
            raise ContextError("update.material_id 不得重复: {}".format(material_id))
        seen.add(material_id)
        status = require_text(material, "status", field)
        if status not in MATERIAL_STATUSES:
            raise ContextError("{}.status 不是受支持的材料状态".format(field))
        normalized = {
            "material_id": material_id,
            "title": require_text(material, "title", field),
            "version": require_text(material, "version", field),
            "material_subtype": require_text(material, "material_subtype", field),
            "status": status,
        }
        for optional in ("source_id", "content_digest"):
            if optional in material:
                normalized[optional] = require_text(material, optional, field)
        materials.append(normalized)
    return materials


def validate_relationships(raw_relationships):
    if not isinstance(raw_relationships, list):
        raise ContextError("update.relationships 必须是数组")
    relationships = []
    seen = set()
    for index, raw_relationship in enumerate(raw_relationships):
        field = "update.relationships[{}]".format(index)
        relationship = require_mapping(raw_relationship, field)
        reject_unknown_fields(relationship, RELATIONSHIP_FIELDS, field)
        relation_id = require_text(relationship, "relation_id", field)
        if relation_id in seen:
            raise ContextError(
                "update.relation_id 不得重复: {}".format(relation_id)
            )
        seen.add(relation_id)
        relation_type = require_text(relationship, "relation_type", field)
        if relation_type not in RELATION_TYPES:
            raise ContextError(
                "{}.relation_type 不是受支持的材料关系".format(field)
            )
        relationships.append(
            {
                "relation_id": relation_id,
                "from_material_id": require_text(
                    relationship, "from_material_id", field
                ),
                "to_material_id": require_text(
                    relationship, "to_material_id", field
                ),
                "relation_type": relation_type,
                "basis": require_text(relationship, "basis", field),
                "source_material_ids": require_source_material_ids(
                    relationship, field
                ),
            }
        )
    return relationships


def validate_records(category, raw_records):
    if not isinstance(raw_records, list):
        raise ContextError("update.{} 必须是数组".format(category))
    id_field, allowed_fields, required_texts = RECORD_SPECS[category]
    records = []
    seen = set()
    for index, raw_record in enumerate(raw_records):
        field = "update.{}[{}]".format(category, index)
        record = require_mapping(raw_record, field)
        reject_unknown_fields(record, allowed_fields, field)
        record_id = require_text(record, id_field, field)
        if record_id in seen:
            raise ContextError(
                "update.{} 不得重复: {}".format(id_field, record_id)
            )
        seen.add(record_id)
        normalized = {id_field: record_id}
        for text_field in required_texts:
            normalized[text_field] = require_text(record, text_field, field)
        normalized["source_material_ids"] = require_source_material_ids(
            record, field
        )
        records.append(normalized)
    return records


def validate_request(raw_request):
    request = require_mapping(raw_request, "request")
    reject_unknown_fields(request, REQUEST_FIELDS, "request")
    if request.get("schema_version") != SCHEMA_VERSION:
        raise ContextError(
            "request.schema_version 必须为 {}".format(SCHEMA_VERSION)
        )
    project_id = require_text(request, "project_id", "request")

    confirmation = require_mapping(
        request.get("confirmation"), "request.confirmation"
    )
    reject_unknown_fields(
        confirmation, {"status", "actor"}, "request.confirmation"
    )
    status = require_text(confirmation, "status", "request.confirmation")
    if status not in {"confirmed", "rejected", "pending"}:
        raise ContextError("request.confirmation.status 不是受支持的状态")
    actor = require_text(confirmation, "actor", "request.confirmation")
    if actor != "user":
        raise ContextError("request.confirmation.actor 必须为 user")

    expected_revision = request.get("expected_revision")
    if expected_revision is not None and (
        not isinstance(expected_revision, int)
        or isinstance(expected_revision, bool)
        or expected_revision < 0
    ):
        raise ContextError("request.expected_revision 必须是非负整数")

    update = require_mapping(request.get("update"), "request.update")
    reject_unknown_fields(update, UPDATE_FIELDS, "request.update")
    if not update or not any(update.values()):
        raise ContextError("request.update 必须至少包含一项更新")

    normalized_update = {}
    for category, raw_records in update.items():
        if category == "materials":
            normalized_update[category] = validate_materials(raw_records)
        elif category == "relationships":
            normalized_update[category] = validate_relationships(raw_records)
        else:
            normalized_update[category] = validate_records(
                category, raw_records
            )
    return {
        "project_id": project_id,
        "expected_revision": expected_revision,
        "confirmation_status": status,
        "update": normalized_update,
    }


def new_package(project_id):
    package = {
        "schema_version": SCHEMA_VERSION,
        "artifact_type": ARTIFACT_TYPE,
        "project_id": project_id,
        "revision": 0,
        "storage": "local_file",
        "external_services": "disabled",
        "last_updated_at": None,
    }
    for collection in PACKAGE_COLLECTIONS:
        package[collection] = []
    return package


def validate_package(package):
    package = require_mapping(package, "project_context")
    if package.get("schema_version") != SCHEMA_VERSION:
        raise ContextError(
            "project_context.schema_version 必须为 {}".format(
                SCHEMA_VERSION
            )
        )
    if package.get("artifact_type") != ARTIFACT_TYPE:
        raise ContextError("project_context.artifact_type 不受支持")
    if package.get("storage") != "local_file":
        raise ContextError("project_context.storage 必须为 local_file")
    if package.get("external_services") != "disabled":
        raise ContextError(
            "project_context.external_services 必须为 disabled"
        )
    require_text(package, "project_id", "project_context")
    revision = package.get("revision")
    if (
        not isinstance(revision, int)
        or isinstance(revision, bool)
        or revision < 0
    ):
        raise ContextError("project_context.revision 必须是非负整数")
    for collection in PACKAGE_COLLECTIONS:
        if not isinstance(package.get(collection), list):
            raise ContextError(
                "project_context.{} 必须是数组".format(collection)
            )
    for collection, id_field in (
        ("confirmed_facts", "fact_id"),
        ("confirmed_relationships", "relation_id"),
    ):
        for index, raw_record in enumerate(package[collection]):
            field = "project_context.{}[{}]".format(collection, index)
            record = require_mapping(raw_record, field)
            record_id = require_text(record, id_field, field)
            if record.get("confirmation_status") != "confirmed":
                raise ContextError(
                    "{} 的 confirmation_status 必须为 confirmed: {}".format(
                        field, record_id
                    )
                )
    sensitive_paths = find_sensitive_paths(package)
    if sensitive_paths:
        raise ContextError(
            "现有项目上下文包包含禁止持久化信息（paths: {}）".format(
                ", ".join(sensitive_paths)
            ),
            "persistence_rejected_sensitive_data",
        )
    return package


def load_package(context_path, project_id):
    if not context_path.exists():
        return new_package(project_id)
    if context_path.is_symlink():
        raise ContextError("project_context 不接受符号链接路径")
    try:
        package = json.loads(context_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ContextError("project_context 无法读取或不是有效 JSON") from exc
    package = validate_package(package)
    if package["project_id"] != project_id:
        raise ContextError(
            "项目上下文包的 project_id 与请求不一致",
            "project_isolation_violation",
        )
    return package


def merge_by_id(existing, incoming, id_field):
    positions = {
        item[id_field]: index
        for index, item in enumerate(existing)
        if isinstance(item, dict) and id_field in item
    }
    for item in incoming:
        if item[id_field] in positions:
            existing[positions[item[id_field]]] = item
        else:
            positions[item[id_field]] = len(existing)
            existing.append(item)


def material_dependencies(item, collection):
    dependencies = set(item.get("source_material_ids", []))
    if collection == "confirmed_relationships":
        dependencies.update(
            {
                item.get("from_material_id"),
                item.get("to_material_id"),
            }
        )
    dependencies.discard(None)
    return dependencies


def set_pending_review(item, stale_material_ids):
    previous = set(item.get("stale_due_to_material_ids", []))
    item["review_status"] = "pending_review"
    item["stale_due_to_material_ids"] = sorted(
        previous | set(stale_material_ids)
    )


def mark_stale(package, changed_material_ids):
    direct_targets = (
        ("confirmed_facts", "fact_id", "fact_ids"),
        ("confirmed_relationships", "relation_id", "relation_ids"),
        ("decisions", "decision_id", "decision_ids"),
        ("conclusions", "conclusion_id", "conclusion_ids"),
        ("conflicts", "conflict_id", "conflict_ids"),
    )
    invalidated = {"material_ids": sorted(changed_material_ids)}
    stale_materials_by_ref = {}
    record_by_ref = {}
    result_field_by_ref = {}
    for collection, id_field, result_field in direct_targets:
        invalidated[result_field] = []
        for item in package[collection]:
            record_id = item[id_field]
            record_by_ref[record_id] = item
            result_field_by_ref[record_id] = result_field
            stale_material_ids = (
                material_dependencies(item, collection)
                & changed_material_ids
            )
            if not stale_material_ids:
                continue
            set_pending_review(item, stale_material_ids)
            invalidated[result_field].append(record_id)
            stale_materials_by_ref[record_id] = set(stale_material_ids)
        invalidated[result_field].sort()

    invalidated["trace_ids"] = []
    trace_stale_materials = {}
    changed = True
    while changed:
        changed = False
        for trace in package["trace_links"]:
            trace_id = trace["trace_id"]
            direct_stale_materials = (
                material_dependencies(trace, "trace_links")
                & changed_material_ids
            )
            from_stale_materials = stale_materials_by_ref.get(
                trace["from_ref"], set()
            )
            to_stale_materials = stale_materials_by_ref.get(
                trace["to_ref"], set()
            )
            trace_materials = (
                direct_stale_materials
                | from_stale_materials
                | to_stale_materials
            )
            previous_trace_materials = trace_stale_materials.get(
                trace_id, set()
            )
            if trace_materials - previous_trace_materials:
                set_pending_review(trace, trace_materials)
                trace_stale_materials[trace_id] = set(trace_materials)
                if trace_id not in invalidated["trace_ids"]:
                    invalidated["trace_ids"].append(trace_id)
                changed = True

            propagated_materials = (
                direct_stale_materials | from_stale_materials
            )
            if not propagated_materials:
                continue
            target_ref = trace["to_ref"]
            target = record_by_ref.get(target_ref)
            result_field = result_field_by_ref.get(target_ref)
            if target is None:
                continue
            previous_target_materials = stale_materials_by_ref.get(
                target_ref, set()
            )
            updated_target_materials = (
                previous_target_materials | propagated_materials
            )
            if updated_target_materials == previous_target_materials:
                continue
            set_pending_review(target, updated_target_materials)
            if target_ref not in invalidated[result_field]:
                invalidated[result_field].append(target_ref)
            stale_materials_by_ref[target_ref] = updated_target_materials
            changed = True

    for result_field in invalidated:
        if result_field != "material_ids":
            invalidated[result_field].sort()
    return invalidated


def confirmed_record(record):
    item = deepcopy(record)
    item["confirmation_status"] = "confirmed"
    item["review_status"] = "current"
    item.pop("stale_due_to_material_ids", None)
    return item


def validate_material_references(package, update):
    material_ids = {
        material["material_id"] for material in package["materials"]
    }
    material_ids.update(
        material["material_id"] for material in update.get("materials", [])
    )
    for category, records in update.items():
        if category == "materials":
            continue
        for record in records:
            references = set(record.get("source_material_ids", []))
            if category == "relationships":
                references.update(
                    {
                        record["from_material_id"],
                        record["to_material_id"],
                    }
                )
            missing = sorted(references - material_ids)
            if missing:
                raise ContextError(
                    "update.{} 引用了不存在的材料: {}".format(
                        category, ", ".join(missing)
                    )
                )


def apply_update(package, update):
    result = deepcopy(package)
    validate_material_references(result, update)

    current_materials = {
        item["material_id"]: item for item in result["materials"]
    }
    changed_material_ids = set()
    for material in update.get("materials", []):
        current = current_materials.get(material["material_id"])
        if current is not None:
            comparable_current = {
                key: current.get(key) for key in MATERIAL_FIELDS
                if key in current
            }
            if comparable_current != material:
                changed_material_ids.add(material["material_id"])

    invalidated = mark_stale(result, changed_material_ids)
    for category, records in update.items():
        target = COLLECTION_TARGETS[category]
        if category == "materials":
            prepared = [confirmed_record(item) for item in records]
            id_field = "material_id"
        elif category == "relationships":
            prepared = [confirmed_record(item) for item in records]
            id_field = "relation_id"
        else:
            id_field = RECORD_SPECS[category][0]
            prepared = [confirmed_record(item) for item in records]
        merge_by_id(result[target], prepared, id_field)

    result["revision"] += 1
    result["last_updated_at"] = datetime.now(timezone.utc).isoformat()
    return result, invalidated


def write_package(context_path, package):
    parent = context_path.parent
    if not parent.is_dir():
        raise ContextError("project_context 的父目录不存在")
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".{}.".format(context_path.name),
        suffix=".tmp",
        dir=str(parent),
    )
    try:
        os.chmod(temporary_name, 0o600)
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            descriptor = None
            json.dump(package, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, context_path)
    except Exception:
        if descriptor is not None:
            os.close(descriptor)
        try:
            os.unlink(temporary_name)
        except FileNotFoundError:
            pass
        raise


def read_request(path):
    if path == "-":
        return json.load(sys.stdin)
    return json.loads(Path(path).read_text(encoding="utf-8"))


def confirmation_status(raw_request):
    if not isinstance(raw_request, dict):
        return None
    confirmation = raw_request.get("confirmation")
    if not isinstance(confirmation, dict):
        return None
    return confirmation.get("status")


def build_result(project_id, status, reason=None, revision=None, invalidated=None):
    persistence = {"status": status}
    if reason is not None:
        persistence["reason"] = reason
    if revision is not None:
        persistence["revision"] = revision
    if invalidated is not None:
        persistence["invalidated"] = invalidated
    return {
        "schema_version": SCHEMA_VERSION,
        "project_id": project_id,
        "persistence": persistence,
    }


def run(raw_request, context_path=None):
    if (
        context_path is not None
        and confirmation_status(raw_request) == "confirmed"
    ):
        sensitive_paths = find_sensitive_paths(raw_request)
        if sensitive_paths:
            raise ContextError(
                "检测到禁止持久化信息；请移除后重试（paths: {}）".format(
                    ", ".join(sensitive_paths)
                ),
                "persistence_rejected_sensitive_data",
            )

    request = validate_request(raw_request)
    project_id = request["project_id"]
    status = request["confirmation_status"]
    if context_path is None:
        return build_result(
            project_id,
            "not_requested",
            reason="single_task_without_persistence",
        )
    package = load_package(context_path, project_id)
    if status in {"rejected", "pending"}:
        return build_result(project_id, status, reason="no_file_change")

    expected_revision = request["expected_revision"]
    if (
        expected_revision is not None
        and package["revision"] != expected_revision
    ):
        raise ContextError(
            "project_context revision 与 expected_revision 不一致",
            "revision_conflict",
        )
    updated, invalidated = apply_update(package, request["update"])
    write_package(context_path, updated)
    return build_result(
        project_id,
        "saved",
        revision=updated["revision"],
        invalidated=invalidated,
    )


def main():
    parser = argparse.ArgumentParser(
        description="维护可选、用户确认且项目隔离的本地项目上下文包。"
    )
    parser.add_argument("request", help="请求 JSON 文件；使用 - 从标准输入读取")
    parser.add_argument(
        "--context",
        type=Path,
        help="可选本地上下文包路径；省略时不持久化",
    )
    args = parser.parse_args()

    try:
        result = run(read_request(args.request), args.context)
    except ContextError as exc:
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
