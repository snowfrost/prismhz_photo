#!/usr/bin/env python3
"""Standard-library prompt contract checks. No model calls or image QA."""
import argparse
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROLES = ("attach_to_prompt", "style_reference", "image_prompt")
PARAM = re.compile(r"(?<!\S)--([a-z][a-z0-9-]*)(?:\s+([\s\S]*?))?(?=\s+--[a-z]|$)")


def parameters(prompt):
    result = {}
    for match in PARAM.finditer(prompt):
        result.setdefault(match[1], []).append((match[2] or "").strip())
    return result


def scene_text(prompt):
    return re.split(r"\s+--[a-z]", prompt, maxsplit=1)[0].strip()


def is_url(value):
    if not isinstance(value, str):
        return False
    parsed = urlparse(value)
    return parsed.scheme in ("https", "http") and bool(parsed.netloc)


def validate(data):
    errors = []
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        return ["root: expected schema_version 1 object"]
    cases = data.get("cases")
    if not isinstance(cases, list) or not cases:
        return ["root: cases must be a nonempty list"]
    seen = set()
    for index, case in enumerate(cases):
        label = f"case[{index}]"

        def check(condition, message):
            if not condition:
                errors.append(f"{label}: {message}")

        if not isinstance(case, dict):
            check(False, "expected object")
            continue
        cid = case.get("id")
        if isinstance(cid, str) and cid:
            label = cid
            check(cid not in seen, "duplicate id")
            seen.add(cid)
        else:
            check(False, "missing string id")
        for key in ("title", "idea", "intent"):
            check(isinstance(case.get(key), str) and bool(case.get(key, "").strip()), f"missing {key}")
        ratio = case.get("ratio", "")
        check(isinstance(ratio, str) and bool(re.fullmatch(r"[1-9]\d*:[1-9]\d*", ratio)), "invalid ratio")
        check(case.get("validation_level") == "prompt_only", "cannot claim visual validation from this contract")
        setup = case.get("reference_setup")
        if not isinstance(setup, dict):
            check(False, "missing reference_setup")
            setup = {}
        for role in ROLES:
            ref = setup.get(role)
            if not isinstance(ref, dict):
                check(False, f"missing reference role {role}")
                continue
            mode, assets = ref.get("mode"), ref.get("assets")
            valid_modes = ("none", "ui", "url", "code") if role == "style_reference" else ("none", "ui", "url")
            check(mode in valid_modes, f"invalid mode for {role}")
            if not isinstance(assets, list) or not all(isinstance(x, str) and x.strip() for x in assets):
                check(False, f"invalid assets for {role}")
                continue
            check((mode == "none" and not assets) or (mode != "none" and bool(assets)), f"asset availability mismatch for {role}")
            if mode == "url":
                check(all(is_url(x) for x in assets), f"{role} needs actual HTTP(S) URLs, not local paths")
            if mode == "code":
                check(all(re.fullmatch(r"[A-Za-z0-9-]+", x) and x != "random" for x in assets), "style code must be explicit, not random")
            if role == "attach_to_prompt":
                check(len(assets) <= 4, "Attach to prompt supports at most four references in checked docs")
        board = case.get("moodboard")
        if not isinstance(board, dict):
            board = {}
        check(board.get("mode") in ("ui", "code"), "moodboard mode must be ui or code")
        check(board.get("source") in ("user_supplied", "user_existing_board", "setup_required"), "unknown moodboard source")
        if board.get("mode") == "code":
            check(board.get("source") == "user_supplied", "code requires user-supplied provenance")
            check(isinstance(board.get("code"), str) and bool(re.fullmatch(r"[A-Za-z0-9-]+", board.get("code", ""))), "invalid board code")
        else:
            check(board.get("code") is None, "UI mode must not invent a board code")
        anchors = {}
        for lang in ("en", "zh"):
            value = case.get(f"anchors_{lang}")
            if not isinstance(value, list) or not 2 <= len(value) <= 5 or not all(isinstance(x, str) and x.strip() for x in value):
                check(False, f"anchors_{lang} must contain 2-5 substantive strings")
                value = []
            anchors[lang] = value
        mj_prompts = []
        for key in ("mj_with_moodboard", "mj_without_moodboard"):
            output = case.get(key)
            if not isinstance(output, dict):
                check(False, f"missing {key}")
                continue
            prompt, note = output.get("prompt"), output.get("setup_note")
            if not isinstance(prompt, str) or not prompt.strip():
                check(False, f"missing prompt for {key}")
                continue
            mj_prompts.append(prompt)
            flags = parameters(prompt)
            check(output.get("reference_setup") == setup, f"{key} silently changes reference roles")
            check(isinstance(note, str) and bool(note.strip()), f"missing reference note for {key}")
            note = note if isinstance(note, str) else ""
            check("Attach to prompt" in note and "Style reference" in note, f"{key} must mention both requested reference roles")
            check(prompt.endswith("--v 8.2"), f"{key} must end exactly --v 8.2")
            check(flags.get("v") == ["8.2"], f"{key} duplicate or wrong version")
            check(flags.get("ar") == [ratio], f"{key} ratio mismatch")
            check(all(len(v) == 1 for v in flags.values()), f"{key} duplicate parameters")
            check(not any(x in flags for x in ("version", "aspect", "profile", "personalize", "personalization")), f"{key} use canonical v/ar/p fields for this audit")
            check(not any(x in flags for x in ("oref", "cref")), f"{key} carries old identity-reference syntax")
            check(not re.search(r"<[^>]+>|\[?(?:YOUR_|TODO|PLACEHOLDER)|https?://(?:example\.|your[-.])", prompt, re.I), f"{key} contains a placeholder")
            check(not re.search(r"[A-Za-z]:[\\/]", prompt), f"{key} contains a local Windows path")
            check(not re.search(r"[\u4e00-\u9fff]", scene_text(prompt)), f"{key} expected English prompt")
            for anchor in anchors["en"]:
                check(anchor.casefold() in scene_text(prompt).casefold(), f"{key} missing shared anchor: {anchor}")
            if key == "mj_with_moodboard":
                check("sw" not in flags and "sv" not in flags, "Moodboard incompatible with sw/sv")
                if board.get("mode") == "code":
                    check(flags.get("p") == [board.get("code")], "Moodboard code is not the supplied code")
                else:
                    check("p" not in flags, "unknown board must use UI, not bare or invented p")
                    check("Personalization" in note and "选择" in note, "UI board setup note missing")
                if board.get("source") == "setup_required":
                    check("已有" not in note and ("准备" in note or "创建" in note), "unavailable board requires an honest setup prerequisite")
            else:
                check("p" not in flags, "no-board prompt contains personalization")
                check("关闭" in note and "Personalization" in note, "no-board note must disable automatic personalization")
            for role, flag in (("attach_to_prompt", "edit"), ("style_reference", "sref")):
                ref = setup.get(role) if isinstance(setup.get(role), dict) else {}
                if ref.get("mode") in ("url", "code"):
                    check(flags.get(flag) == [" ".join(ref.get("assets", []))], f"{flag} differs from supplied reference assets")
                else:
                    check(flag not in flags, f"{flag} invented without actual URL/code")
            image_ref = setup.get("image_prompt") if isinstance(setup.get("image_prompt"), dict) else {}
            if "iw" in flags:
                check(image_ref.get("mode") in ("ui", "url"), "iw applies to Image Prompt, not Attach to prompt")
            if image_ref.get("mode") == "url":
                check(prompt.startswith(" ".join(image_ref.get("assets", [])) + " "), "Image Prompt URLs must prefix text")
        if len(mj_prompts) == 2:
            check(scene_text(mj_prompts[0]).casefold() != scene_text(mj_prompts[1]).casefold(), "dual versions only differ in parameters")
        ig = case.get("imagegen")
        ig = ig if isinstance(ig, dict) else {}
        text = ig.get("prompt")
        if not isinstance(text, str) or not text.strip():
            check(False, "missing ImageGen prompt")
            continue
        check(bool(re.search(r"[\u4e00-\u9fff]", text)), "ImageGen must be native Chinese")
        check(not re.search(r"--[A-Za-z]", text), "ImageGen contains MJ flags")
        check(isinstance(ratio, str) and ratio in text, "ImageGen ratio missing")
        for anchor in anchors["zh"]:
            check(anchor in text, f"ImageGen missing shared anchor: {anchor}")
    return errors


def to_markdown(data):
    lines = ["# 镜花水月 · 双 MJ 与 ImageGen 示例", "", data.get("note", "新写提示词，未进行出图实测。"), ""]
    display = {"attach_to_prompt": "Attach to prompt", "style_reference": "Style reference", "image_prompt": "Image Prompt"}
    for case in data["cases"]:
        lines.extend([f"## {case['title']}｜{case['ratio']}", "", case["intent"], ""])
        for key, label in (("mj_with_moodboard", "MJ｜有情绪版"), ("mj_without_moodboard", "MJ｜无情绪版")):
            block = case[key]
            lines.extend([f"### {label}", "", "```text", block["prompt"], "```", "", block["setup_note"], ""])
            for role, ref in block["reference_setup"].items():
                lines.append(f"- {display[role]}：" + ("不使用。" if ref["mode"] == "none" else "、".join(ref["assets"]) + f"（{ref['mode']}）。"))
            lines.append("")
        lines.extend(["### ImageGen｜中文", "", "```text", case["imagegen"]["prompt"], "```", ""])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--markdown", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
        errors = validate(data)
    except (OSError, ValueError, TypeError, KeyError) as exc:
        data, errors = {}, [f"Invalid input: {exc}"]
    report = {"status": "FAIL" if errors else "PASS", "case_count": len(data.get("cases", [])) if isinstance(data.get("cases"), list) else 0, "scope": "prompt-contract only; no image generation or account validation", "errors": errors}
    if args.markdown:
        if args.markdown.resolve() == args.input.resolve():
            parser.error("markdown output must not overwrite input")
        if not errors:
            args.markdown.parent.mkdir(parents=True, exist_ok=True)
            args.markdown.write_text(to_markdown(data), encoding="utf-8")
    if args.report:
        if args.report.resolve() == args.input.resolve() or (args.markdown and args.report.resolve() == args.markdown.resolve()):
            parser.error("report must have a distinct output path")
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
