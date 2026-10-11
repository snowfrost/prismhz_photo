#!/usr/bin/env python3
"""Validate a saved western-imperial-fantasy prompt response."""

import re
import sys
from pathlib import Path


REQUIRED_HEADINGS = (
    "### 画面设计",
    "### ImageGen 中文提示词",
    "### Midjourney 8.2 Prompt",
    "### 负面约束",
)


def section(text, heading, next_headings):
    start = text.find(heading)
    if start < 0:
        return ""
    start += len(heading)
    ends = [text.find(h, start) for h in next_headings]
    ends = [value for value in ends if value >= 0]
    end = min(ends) if ends else len(text)
    value = text[start:end].strip()
    value = re.sub(r"^```(?:text)?\s*", "", value)
    value = re.sub(r"\s*```\s*$", "", value)
    return value.strip()


def main():
    if len(sys.argv) != 2:
        raise SystemExit("Usage: validate_outputs.py <output.md>")
    path = Path(sys.argv[1])
    text = path.read_text(encoding="utf-8-sig")
    errors = []
    warnings = []

    for heading in REQUIRED_HEADINGS:
        if heading not in text:
            errors.append(f"missing heading: {heading}")

    imagegen = section(text, REQUIRED_HEADINGS[1], REQUIRED_HEADINGS[2:])
    midjourney = section(text, REQUIRED_HEADINGS[2], REQUIRED_HEADINGS[3:])
    negative = section(text, REQUIRED_HEADINGS[3], ("### 可调选项",))

    if not imagegen:
        errors.append("empty ImageGen prompt")
    if not midjourney:
        errors.append("empty Midjourney prompt")
    if not negative:
        errors.append("empty negative constraints")

    if re.search(r"--(?:ar|v|s|c|raw|no|hd)\b", imagegen):
        errors.append("ImageGen prompt contains Midjourney syntax")
    if midjourney and not midjourney.endswith("--v 8.2"):
        errors.append("Midjourney prompt must end exactly with --v 8.2")
    if "--hd" in midjourney:
        errors.append("Midjourney prompt contains disallowed --hd")
    if re.search(r"--(?:sref|oref|seed|profile)\b", midjourney):
        warnings.append("reference, seed, or profile parameter present; verify it came from the user")
    if len(imagegen) < 180:
        warnings.append("ImageGen prompt is unusually short")
    if len(midjourney.split()) < 90:
        warnings.append("Midjourney prompt is unusually short")
    if not re.search(r"imperial|royal|Gothic|throne|palace|fortress|court", midjourney, re.I):
        warnings.append("Midjourney prompt lacks an explicit imperial/Gothic anchor")
    if not re.search(r"platinum|antique gold|gilded|obsidian|black velvet|mirror water", midjourney, re.I):
        warnings.append("Midjourney prompt lacks the house material system")
    todo_marker = "[" + "TO" + "DO"
    todo_label = "TO" + "DO:"
    if todo_marker in text or todo_label in text:
        errors.append("unfinished TODO placeholder")

    print(f"FILE={path}")
    print(f"ERRORS={len(errors)}")
    print(f"WARNINGS={len(warnings)}")
    for message in errors:
        print(f"ERROR: {message}")
    for message in warnings:
        print(f"WARNING: {message}")
    if errors:
        raise SystemExit(1)
    print("VALID")


if __name__ == "__main__":
    main()
