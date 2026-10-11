#!/usr/bin/env python3
"""Validate the bundled Moodboard-assisted evidence mapping."""

from __future__ import annotations

import json
import hashlib
import re
import sys
from pathlib import Path


EXPECTED_MAPPING = {
    "01": "08",
    "02": "04",
    "03": "10",
    "04": "02",
    "05": "07",
    "06": "03",
    "07": "12",
    "08": "06",
    "09": "05",
}

EXPECTED_VALIDATED = {"02", "03", "04", "05", "06", "07", "08", "10", "12"}
EXPECTED_PROMPT_ONLY = {"01", "09", "11"}


def main() -> int:
    source = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else Path(__file__).resolve().parents[1] / "references" / "evidence-map.json"
    )
    try:
        data = json.loads(source.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"INVALID: {exc}", file=sys.stderr)
        return 2

    errors: list[str] = []
    if data.get("validation_scope") != "Moodboard-assisted Midjourney generation only":
        errors.append("validation_scope must remain Moodboard-assisted only")
    if data.get("moodboard", {}).get("specific_id_or_code_captured") is not False:
        errors.append("the current package must not claim a captured Moodboard code")
    if len(data.get("source_reference_labels", [])) != 12:
        errors.append("expected 12 source reference labels")

    outputs = data.get("validated_outputs", [])
    actual_mapping = {item.get("output_index"): item.get("prompt_number") for item in outputs}
    if actual_mapping != EXPECTED_MAPPING:
        errors.append(f"output-to-prompt mapping differs: {actual_mapping}")

    for item in outputs:
        if not re.fullmatch(r"[0-9a-f]{64}", item.get("sha256", "")):
            errors.append(f"invalid sha256 for output {item.get('output_index')}")

    status = data.get("prompt_status", {})
    validated = set(status.get("moodboard_assisted_visual_validation", []))
    prompt_only = set(status.get("prompt_only_not_visually_validated", []))
    if validated != EXPECTED_VALIDATED:
        errors.append("validated prompt set differs")
    if prompt_only != EXPECTED_PROMPT_ONLY:
        errors.append("prompt-only set differs")
    if validated & prompt_only or validated | prompt_only != {f"{n:02d}" for n in range(1, 13)}:
        errors.append("prompt validation sets must be disjoint and cover 01-12")

    skill_root = Path(__file__).resolve().parents[1]
    board_path = skill_root / data.get("output_board_asset", "")
    if not board_path.is_file():
        errors.append("Moodboard-assisted output board asset is missing")
    else:
        board_sha256 = hashlib.sha256(board_path.read_bytes()).hexdigest()
        if board_sha256 != data.get("output_board_sha256"):
            errors.append("output board sha256 differs")

    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1

    print("VALID")
    print("- 12 source references recorded")
    print("- 9 Moodboard-assisted output mappings verified")
    print("- 3 prompt-only items and ImageGen boundary preserved")
    print("- output board asset hash verified")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
