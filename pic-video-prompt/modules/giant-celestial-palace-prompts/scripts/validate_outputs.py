#!/usr/bin/env python3
"""Validate saved output from giant-celestial-palace-prompts.

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
)

FORBIDDEN_UNLESS_USER_SUPPLIED = (
    "--sref",
    "--oref",
    "--seed",
    "--profile",
    "--p ",
    "--hd",
)


def load_text(source: str) -> str:
    if source == "-":
        return sys.stdin.read()
    return Path(source).read_text(encoding="utf-8")


def validate(text: str, allow_reference_params: bool = False) -> list[str]:
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
                    + line[:160]
                )

    if re.search(r"--v\s+(?!8\.2(?:\s|$))\S+", text):
        errors.append("a non-8.2 Midjourney version was found")

    if not allow_reference_params:
        lowered = text.lower()
        for token in FORBIDDEN_UNLESS_USER_SUPPLIED:
            if token in lowered:
                errors.append(f"unexpected parameter without explicit user input: {token.strip()}")

    urls = re.findall(r"https?://\S+", text)
    if urls:
        errors.append("output contains URL(s); do not invent image or style-reference URLs")

    if not re.search(r"--ar\s+\d+:\d+", text):
        errors.append("Midjourney prompt is missing a valid --ar W:H parameter")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", help="UTF-8 output file, or - for stdin")
    parser.add_argument(
        "--allow-reference-params",
        action="store_true",
        help="Allow user-supplied --sref/--oref/--seed/--profile/--hd parameters.",
    )
    args = parser.parse_args()

    try:
        text = load_text(args.source)
    except (OSError, UnicodeError) as exc:
        print(f"INVALID: cannot read input: {exc}", file=sys.stderr)
        return 2

    errors = validate(text, allow_reference_params=args.allow_reference_params)
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
