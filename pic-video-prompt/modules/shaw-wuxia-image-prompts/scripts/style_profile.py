#!/usr/bin/env python3
"""Return the canonical Shaw-wuxia prompt profile for a mode or alias."""

from __future__ import annotations

import argparse
import json
import sys


PROFILES = {
    "modern-lone-wuxia": {
        "label_zh": "邵氏孤侠自然主义",
        "aliases": ["邵氏电影风", "邵氏孤侠", "孤独剑客", "独行侠客", "自然主义孤侠"],
        "visual_thesis": "A weathered traveler is reduced against beautiful quiet nature; serenity makes solitude legible.",
        "anchors": [
            "environment-dominant widescreen composition",
            "one restrained traveler displaced from center",
            "natural fibers and low-amplitude motion physics",
            "low-saturation color field with a bounded warm accent",
            "atmospheric depth and restrained grain",
        ],
        "nearest_drift": ["oversized costume portrait", "extra companion", "duplicate weapon", "fantasy portal"],
    },
    "studio-classic": {
        "label_zh": "邵氏棚拍古典",
        "aliases": ["老邵氏", "七十年代邵氏", "棚拍武侠", "人工山水", "绘景武侠", "唯美古龙"],
        "visual_thesis": "Figures move through an intentionally crafted jianghu of layered sets, controlled color and theatrical light.",
        "anchors": [
            "widescreen graphic blocking",
            "crafted rocks, architecture or garden layers",
            "painted atmospheric depth",
            "controlled jewel-color accents",
            "theatrical side light, gentle bloom and fine color grain",
        ],
        "nearest_drift": ["generic outdoor realism", "plastic theme-park set", "magical portal spectacle"],
    },
    "action-wuxia": {
        "label_zh": "邵氏动作武侠",
        "aliases": ["邵氏打斗", "邵氏武打", "阳刚武侠", "动作武侠", "决斗", "围攻"],
        "visual_thesis": "Conflict is made legible through body-to-space geometry, decisive silhouettes and controlled color.",
        "anchors": [
            "readable arena and opponent spacing",
            "clear feet, eyelines and weapon directions",
            "one owned weapon relation per fighter",
            "bounded red accent and strong separation light",
            "action continuity without effects-heavy spectacle",
        ],
        "nearest_drift": ["crowded unreadable melee", "duplicate limbs or weapons", "superhero pose", "xianxia energy effects"],
    },
}


def normalize(text: str) -> str:
    return "".join(text.strip().lower().split())


def resolve(query: str) -> tuple[str | None, str]:
    normalized = normalize(query)
    for mode, profile in PROFILES.items():
        if normalized == normalize(mode) or any(normalized == normalize(alias) for alias in profile["aliases"]):
            return mode, "exact"
    for mode, profile in PROFILES.items():
        candidates = [mode, *profile["aliases"]]
        if any(normalize(candidate) in normalized or normalized in normalize(candidate) for candidate in candidates):
            return mode, "substring"
    if any(token in query for token in ("打", "斗", "决", "围攻", "招式")):
        return "action-wuxia", "inferred"
    if any(token in query for token in ("棚", "老邵氏", "人工", "绘景", "古龙")):
        return "studio-classic", "inferred"
    if "邵氏" in query or any(token in query for token in ("孤侠", "剑客", "独行")):
        return "modern-lone-wuxia", "default"
    return None, "none"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("query", help="Canonical mode or Chinese alias")
    parser.add_argument("--all", action="store_true", help="Return all profiles")
    args = parser.parse_args()

    if args.all:
        print(json.dumps({"status": "PASS", "profiles": PROFILES}, ensure_ascii=False, indent=2))
        return 0

    mode, match_type = resolve(args.query)
    if mode is None:
        print(json.dumps({"status": "NO_MATCH", "query": args.query}, ensure_ascii=False, indent=2))
        return 2

    print(
        json.dumps(
            {
                "status": "PASS",
                "query": args.query,
                "canonical_mode": mode,
                "match_type": match_type,
                "profile": PROFILES[mode],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())

