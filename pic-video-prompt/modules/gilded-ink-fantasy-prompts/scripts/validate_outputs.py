#!/usr/bin/env python3
"""Validate saved output from gilded-ink-fantasy-prompts.

Usage:
    python validate_outputs.py output.md
    type output.md | python validate_outputs.py -
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


REQUIRED_SECTIONS = (
    "画面设计",
    "ImageGen Prompt",
    "Midjourney 8.2 Prompt",
    "可调选项",
)

FORBIDDEN_UNLESS_USER_SUPPLIED = (
    "--sref",
    "--oref",
    "--seed",
    "--profile",
    "--p ",
    "--hd",
)

PLACEHOLDERS = (
    "[TODO",
    "<TODO",
    "PLACEHOLDER",
)

HUMAN_HAIR_ORNAMENT_TERMS = (
    "发簪",
    "发梳",
    "步摇",
    "头冠",
    "冠饰",
    "簪梳",
    "hairpin",
    "hair comb",
    "headpiece",
    "headdress",
    "diadem",
)

HUMAN_GARMENT_STRUCTURE_TERMS = (
    "内层",
    "中层",
    "外层",
    "水袖",
    "衣领",
    "袖口",
    "裙摆",
    "inner layer",
    "middle robe",
    "outer robe",
    "water sleeves",
    "collar",
    "cuffs",
    "hem",
)

HUMAN_TEXTILE_TERMS = (
    "丝绸",
    "锦缎",
    "薄纱",
    "欧根纱",
    "silk",
    "brocade",
    "gauze",
    "organza",
)


def load_text(source: str) -> str:
    if source == "-":
        return sys.stdin.read()
    return Path(source).read_text(encoding="utf-8")


def validate(
    text: str,
    allow_reference_params: bool = False,
    require_human_styling: bool = False,
) -> list[str]:
    errors: list[str] = []

    for section in REQUIRED_SECTIONS:
        if section not in text:
            errors.append(f"missing required section: {section}")

    version_lines = [line.strip() for line in text.splitlines() if "--v" in line]
    if not version_lines:
        errors.append("no Midjourney version parameter found")
    else:
        for line in version_lines:
            if not re.search(r"--v\s+8\.2\s*$", line):
                errors.append(
                    "every line containing --v must end exactly with '--v 8.2': "
                    + line[:180]
                )

    if re.search(r"--v\s+(?!8\.2(?:\s|$))\S+", text):
        errors.append("a non-8.2 Midjourney version was found")

    if not allow_reference_params:
        lowered = text.lower()
        for token in FORBIDDEN_UNLESS_USER_SUPPLIED:
            if token in lowered:
                errors.append(
                    f"unexpected parameter without explicit user input: {token.strip()}"
                )

    if re.findall(r"https?://\S+", text):
        errors.append("output contains URL(s); do not invent reference URLs")

    if not re.search(r"--ar\s+\d+:\d+", text):
        errors.append("Midjourney prompt is missing a valid --ar W:H parameter")

    for placeholder in PLACEHOLDERS:
        if placeholder.lower() in text.lower():
            errors.append(f"unfinished placeholder found: {placeholder}")

    if require_human_styling:
        lowered = text.lower()
        if not any(term.lower() in lowered for term in HUMAN_HAIR_ORNAMENT_TERMS):
            errors.append(
                "human styling requires a concrete hair ornament or headpiece term"
            )
        if not any(term.lower() in lowered for term in HUMAN_GARMENT_STRUCTURE_TERMS):
            errors.append(
                "human styling requires a concrete garment layer or structural term"
            )
        if not any(term.lower() in lowered for term in HUMAN_TEXTILE_TERMS):
            errors.append("human styling requires at least one textile material term")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="UTF-8 output file, or - for stdin")
    parser.add_argument(
        "--allow-reference-params",
        action="store_true",
        help="Allow explicitly user-supplied reference parameters.",
    )
    parser.add_argument(
        "--require-human-styling",
        action="store_true",
        help="Require concrete hair ornament, garment structure, and textile terms.",
    )
    args = parser.parse_args()

    try:
        text = load_text(args.source)
    except (OSError, UnicodeError) as exc:
        print(f"INVALID: cannot read input: {exc}", file=sys.stderr)
        return 2

    errors = validate(
        text,
        allow_reference_params=args.allow_reference_params,
        require_human_styling=args.require_human_styling,
    )
    if errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
        return 1

    print("VALID")
    print("- required sections present")
    print("- Midjourney version lines end with --v 8.2")
    print("- no unapproved reference/version parameters or URLs found")
    print("- aspect ratio parameter present")
    print("- no unfinished placeholders found")
    if args.require_human_styling:
        print("- concrete human hair ornament and layered textile styling found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
