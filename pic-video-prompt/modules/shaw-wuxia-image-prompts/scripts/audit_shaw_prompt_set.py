#!/usr/bin/env python3
"""Audit a Shaw-wuxia still-image prompt-set manifest."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


VALID_MODES = {"modern-lone-wuxia", "studio-classic", "action-wuxia"}
RATIO_RE = re.compile(r"^[1-9]\d*:[1-9]\d*$")
CHINESE_RE = re.compile(r"[\u3400-\u9fff]")
MJ_TOKENS = ("--ar", "--v", "--raw", "--sref", "--oref", "--seed", "--profile")


def nonempty_string(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def nonempty_list(value: object, minimum: int = 1) -> bool:
    return isinstance(value, list) and len(value) >= minimum and all(nonempty_string(item) for item in value)


def load_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("manifest root must be an object")
    return data


def audit(data: dict) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    for field in ("request", "mode", "ratio"):
        if not nonempty_string(data.get(field)):
            errors.append(f"missing or empty top-level field: {field}")

    mode = data.get("mode")
    if nonempty_string(mode) and mode not in VALID_MODES:
        errors.append(f"unsupported mode: {mode}")

    ratio = data.get("ratio")
    if nonempty_string(ratio) and not RATIO_RE.match(ratio):
        errors.append(f"invalid ratio: {ratio}")

    dna = data.get("series_dna")
    if not isinstance(dna, dict):
        errors.append("series_dna must be an object")
        dna = {}

    for field in (
        "visual_thesis",
        "character_or_subject",
        "composition_grammar",
        "palette_logic",
        "lighting_logic",
        "optical_treatment",
        "emotional_tension",
    ):
        if not nonempty_string(dna.get(field)):
            errors.append(f"missing or empty series_dna.{field}")

    if not nonempty_list(dna.get("style_mode_anchors"), 3):
        errors.append("series_dna.style_mode_anchors must contain at least 3 non-empty anchors")
    if not nonempty_list(dna.get("must_keep"), 2):
        errors.append("series_dna.must_keep must contain at least 2 non-empty anchors")
    if not nonempty_list(dna.get("allowed_variables"), 1):
        errors.append("series_dna.allowed_variables must be a non-empty list")

    frames = data.get("frames")
    if not isinstance(frames, list) or not frames:
        errors.append("frames must be a non-empty list")
        return errors, warnings

    ids: set[str] = set()
    for index, frame in enumerate(frames, start=1):
        prefix = f"frames[{index}]"
        if not isinstance(frame, dict):
            errors.append(f"{prefix} must be an object")
            continue

        for field in (
            "id",
            "title",
            "shot_role",
            "subject_scale",
            "weapon_rule",
            "dominant_relation",
            "midjourney_prompt",
            "imagegen_prompt",
        ):
            if not nonempty_string(frame.get(field)):
                errors.append(f"{prefix}.{field} must be a non-empty string")

        frame_id = frame.get("id")
        if nonempty_string(frame_id):
            if frame_id in ids:
                errors.append(f"duplicate frame id: {frame_id}")
            ids.add(frame_id)

        subject_count = frame.get("subject_count")
        if not isinstance(subject_count, int) or subject_count < 0:
            errors.append(f"{prefix}.subject_count must be a non-negative integer")

        for field, minimum in (
            ("variable_change", 1),
            ("continuity_anchors", 2),
            ("drift_risks", 1),
            ("negative_constraints", 1),
        ):
            if not nonempty_list(frame.get(field), minimum):
                errors.append(f"{prefix}.{field} must contain at least {minimum} non-empty item(s)")

        mj = frame.get("midjourney_prompt", "")
        ig = frame.get("imagegen_prompt", "")
        if nonempty_string(mj):
            if ratio and f"--ar {ratio}" not in mj:
                errors.append(f"{prefix}.midjourney_prompt is missing --ar {ratio}")
            if not mj.rstrip().endswith("--v 8.2"):
                errors.append(f"{prefix}.midjourney_prompt must end exactly with --v 8.2")
            versions = re.findall(r"--v\s+[^\s]+", mj)
            if versions != ["--v 8.2"]:
                errors.append(f"{prefix}.midjourney_prompt must contain exactly one --v 8.2 token")
            if CHINESE_RE.search(mj):
                warnings.append(f"{prefix}.midjourney_prompt contains Chinese characters")

        if nonempty_string(ig):
            lowered = ig.lower()
            for token in MJ_TOKENS:
                if token in lowered:
                    errors.append(f"{prefix}.imagegen_prompt contains Midjourney token {token}")

        if mode == "modern-lone-wuxia" and subject_count == 1:
            risks = " ".join(frame.get("drift_risks", []))
            if not any(term in risks.lower() for term in ("extra", "companion", "多人", "同伴", "second")):
                warnings.append(f"{prefix} does not declare an extra-person drift risk")

    if len(frames) >= 3:
        roles = [frame.get("shot_role") for frame in frames if isinstance(frame, dict)]
        if len(set(roles)) < 2:
            warnings.append("series has fewer than 2 distinct shot roles")

    return errors, warnings


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("manifest", type=Path)
    args = parser.parse_args()

    try:
        data = load_json(args.manifest)
        errors, warnings = audit(data)
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "message": str(exc)}, ensure_ascii=False, indent=2))
        return 2

    result = {
        "status": "VALID" if not errors else "INVALID",
        "mode": data.get("mode"),
        "ratio": data.get("ratio"),
        "frame_count": len(data.get("frames", [])) if isinstance(data.get("frames"), list) else 0,
        "errors": errors,
        "warnings": warnings,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
