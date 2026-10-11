#!/usr/bin/env python3
"""Validate a saved zanhua-lady prompt response.

Usage:
    python validate_outputs.py output.md
    python validate_outputs.py output.md --allow-profile
    python validate_outputs.py output.md --require-profile
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "画面设计",
    "情绪版状态",
    "Midjourney 8.2 Prompt",
    "ImageGen 中文重建提示词",
    "验证边界",
)

PLACEHOLDER_MARKERS = (
    "moodboard_code",
    "moodboard-id",
    "your_code",
    "your-profile",
    "<code>",
    "<mid>",
    "情绪版代码",
    "请填写代码",
)

GENERIC_FILLER = (
    "masterpiece",
    "best quality",
    "8k",
    "16k",
)


def load_text(source: str) -> str:
    if source == "-":
        return sys.stdin.read()
    return Path(source).read_text(encoding="utf-8")


def mj_version_lines(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if "--v" in line]


def section_body(text: str, heading: str) -> str | None:
    match = re.search(
        rf"#{{1,6}}[ \t]+{re.escape(heading)}[ \t]*\n+(.*?)(?=\n+#{{1,6}}[ \t]+|\Z)",
        text,
        flags=re.S,
    )
    return match.group(1).strip() if match else None


def validate(text: str, allow_profile: bool, require_profile: bool) -> list[str]:
    errors: list[str] = []
    lowered = text.lower()

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"missing required section: {section}")

    version_lines = mj_version_lines(text)
    if not version_lines:
        errors.append("no Midjourney version line found")
    for line in version_lines:
        if not re.search(r"--v\s+8\.2\s*$", line):
            errors.append("every --v line must end exactly with '--v 8.2': " + line[:180])
        if not re.search(r"--ar\s+\d+:\d+", line):
            errors.append("Midjourney prompt is missing --ar W:H")

    mj_body = section_body(text, "Midjourney 8.2 Prompt")
    if mj_body:
        mj_word_count = len(re.findall(r"[A-Za-z0-9'-]+", mj_body))
        if mj_word_count > 230:
            errors.append(
                f"Midjourney prompt is too long ({mj_word_count} words; maximum 230)"
            )
        if mj_word_count < 120:
            errors.append(
                f"Midjourney prompt is too short for this style ({mj_word_count} words; minimum 120)"
            )

    profile_matches = re.findall(
        r"(?:--profile|--p)\s+([^\s]+)", "\n".join(version_lines), flags=re.I
    )
    if profile_matches and not allow_profile:
        errors.append("profile parameter found without --allow-profile")
    if require_profile and not profile_matches:
        errors.append("--require-profile was set but no --p/--profile parameter was found")
    for value in profile_matches:
        if any(marker in value.lower() for marker in PLACEHOLDER_MARKERS):
            errors.append(f"profile parameter contains a placeholder: {value}")

    if profile_matches and ("--sw" in lowered or "--sv" in lowered):
        errors.append("Moodboard/profile output must not include --sw or --sv")

    if "--raw" in lowered:
        errors.append("--raw is not part of the default zanhua-lady recipe")

    for filler in GENERIC_FILLER:
        if re.search(rf"\b{re.escape(filler)}\b", lowered):
            errors.append(f"generic quality filler found: {filler}")

    if re.search(r"https?://\S+", text):
        errors.append("URL found; do not invent an Image Prompt URL")

    imagegen_body = section_body(text, "ImageGen 中文重建提示词")
    if imagegen_body and re.search(r"--(?:ar|s|c|p|no|v)\b", imagegen_body):
        errors.append("ImageGen section contains Midjourney syntax")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="UTF-8 Markdown file or - for stdin")
    parser.add_argument(
        "--allow-profile",
        action="store_true",
        help="Allow a user-supplied --p/--profile value.",
    )
    parser.add_argument(
        "--require-profile",
        action="store_true",
        help="Require a user-supplied --p/--profile value.",
    )
    args = parser.parse_args()

    try:
        text = load_text(args.source)
    except (OSError, UnicodeError) as exc:
        print(f"INVALID: cannot read input: {exc}", file=sys.stderr)
        return 2

    errors = validate(text, args.allow_profile, args.require_profile)
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1

    print("VALID")
    print("- required response sections present")
    print("- Midjourney prompt has an aspect ratio and ends with --v 8.2")
    print("- Moodboard code policy and ImageGen syntax boundary respected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
