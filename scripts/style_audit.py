#!/usr/bin/env python3
"""Audit objective writing-style signals without making authorship claims."""

import argparse
import json
import math
import re
from pathlib import Path


T1_PATTERNS = (
    "全面赋能", "行业标杆", "里程碑", "前景广阔", "意义重大",
    "无缝协同", "能力跃迁", "国际领先", "业界领先",
    "综上所述", "值得注意的是", "业内专家一致认为",
    "研究表明", "标志着", "构建新格局",
)
T2_GROUPS = {
    "transition": ("此外", "同时", "与此同时", "进一步", "更重要的是"),
    "rendering": ("全面", "深入", "显著", "卓越", "强大"),
}
T3_WORDS = ("重要", "关键", "核心", "提升")


def _mask_exempt(text: str):
    patterns = (
        re.compile(r"```.*?```", re.DOTALL),
        re.compile(r"`[^`]*`"),
        re.compile(r"“[^”]*”"),
        re.compile(r'"[^"\n]*"'),
        re.compile(r"(?m)^\s*>.*$"),
        re.compile(r"(?m)^\s*(?:示例|反例|禁用词|问题词)(?:示例|说明)?\s*[：:].*$"),
    )
    masked = text
    exempted = 0
    for pattern in patterns:
        masked, count = pattern.subn(lambda match: " " * len(match.group(0)), masked)
        exempted += count
    return masked, exempted


def _cv(values) -> float:
    if not values:
        return 0.0
    mean = sum(values) / len(values)
    if mean == 0:
        return 0.0
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    return math.sqrt(variance) / mean


def audit_text(text: str) -> dict:
    masked, exempted_count = _mask_exempt(text)
    hits = []
    for phrase in T1_PATTERNS:
        for match in re.finditer(re.escape(phrase), masked):
            hits.append({"tier": "T1", "pattern": phrase, "start": match.start(),
                         "context": "body", "occurrences": 1})

    paragraphs = [part.strip() for part in re.split(r"\n\s*\n", masked) if part.strip()]
    for index, paragraph in enumerate(paragraphs, start=1):
        for group, words in T2_GROUPS.items():
            occurrences = [(match.start(), word) for word in words
                           for match in re.finditer(re.escape(word), paragraph)]
            occurrences.sort()
            found = list(dict.fromkeys(word for _, word in occurrences))
            if len(occurrences) >= 2:
                hits.append({
                    "tier": "T2",
                    "pattern": group,
                    "paragraph": index,
                    "matches": found,
                    "occurrences": len(occurrences),
                    "context": "body",
                })

    visible_chars = len(re.sub(r"\s+", "", masked))
    for word in T3_WORDS:
        count = masked.count(word)
        density = count / visible_chars if visible_chars else 0.0
        if count:
            hits.append({"tier": "T3", "pattern": word, "count": count, "density": density,
                         "context": "body", "occurrences": count})

    sentences = [
        part.strip()
        for part in re.split(r"[。！？!?]+", masked)
        if part.strip()
    ]
    sentence_lengths = [len(re.sub(r"\s+", "", sentence)) for sentence in sentences]
    paragraph_lengths = [len(re.sub(r"\s+", "", paragraph)) for paragraph in paragraphs]
    metrics = {
        "character_count": visible_chars,
        "sentence_count": len(sentences),
        "mean_sentence_length": (
            sum(sentence_lengths) / len(sentence_lengths) if sentence_lengths else 0.0
        ),
        "sentence_length_cv": _cv(sentence_lengths),
        "paragraph_count": len(paragraphs),
        "paragraph_length_cv": _cv(paragraph_lengths),
    }
    return {
        "hits": sorted(hits, key=lambda item: (item["tier"], item.get("start", -1),
                                                item.get("paragraph", -1), item["pattern"])),
        "metrics": metrics,
        "summary": {
            "t1": sum(hit["tier"] == "T1" for hit in hits),
            "t2": sum(hit["tier"] == "T2" for hit in hits),
            "t3": sum(hit["tier"] == "T3" for hit in hits),
            "authorship_verdict": "not_applicable",
            "exempted_count": exempted_count,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    args = parser.parse_args()
    try:
        text = Path(args.path).read_text(encoding="utf-8")
    except OSError as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    print(json.dumps(audit_text(text), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
