#!/usr/bin/env python3
"""Finalize one MJ prompt locally. No network calls or image generation."""
import argparse
import re
from pathlib import Path

DEFAULT_PROFILE = 'e1u2l58'
DEFAULT_RATIO = '16:9'
DEFAULT_VERSION = '8.2'
FLAG = re.compile(r'(?<!\S)--([A-Za-z][A-Za-z0-9-]*)\b')
OWNED = {'profile', 'p', 'ar', 'aspect', 'v', 'version'}


def unique_value(entries, names):
    values = [value for name, value, _ in entries if name in names]
    if any(not value for value in values):
        raise ValueError('A parameter is missing its value: ' + ', '.join(sorted(names)))
    if len(set(values)) > 1:
        raise ValueError('Conflicting values: ' + ', '.join(sorted(names)))
    return values[0] if values else None


def finalize(prompt, profile=None, no_profile=False, ratio=None):
    text = prompt.strip()
    if not text or '```' in text:
        raise ValueError('Provide one plain-text English prompt without Markdown fences.')
    if profile is not None and no_profile:
        raise ValueError('Choose either a replacement profile or no profile.')
    matches = list(FLAG.finditer(text))
    body = text[:matches[0].start()].strip() if matches else text
    if not body:
        raise ValueError('The image description is empty.')
    entries = []
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        entries.append((match.group(1).lower(), text[match.end():end].strip(), text[match.start():end].strip()))

    chosen_ratio = ratio if ratio is not None else unique_value(entries, {'ar', 'aspect'}) or DEFAULT_RATIO
    if not re.fullmatch(r'[1-9]\d*:[1-9]\d*', chosen_ratio):
        raise ValueError('Ratio must contain two positive integers, e.g. 16:9.')
    version = unique_value(entries, {'v', 'version'}) or DEFAULT_VERSION
    if not re.fullmatch(r'\d+(?:\.\d+)?', version):
        raise ValueError('Provide a numeric MJ model version.')

    chosen_profile = None
    if not no_profile:
        if profile is not None:
            if not re.fullmatch(r'[A-Za-z0-9_-]+(?: [A-Za-z0-9_-]+)*', profile):
                raise ValueError('Invalid profile value.')
            chosen_profile = profile
        else:
            recorded = unique_value(entries, {'p', 'profile'})
            if recorded is not None and recorded != DEFAULT_PROFILE:
                raise ValueError('A different profile exists; explicitly use --profile VALUE or --no-profile.')
            chosen_profile = DEFAULT_PROFILE

    parts = [body] + [segment for name, _, segment in entries if name not in OWNED]
    parts.append('--ar ' + chosen_ratio)
    if chosen_profile:
        parts.append('--profile ' + chosen_profile)
    parts.append('--v ' + version)
    return ' '.join(parts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', required=True, type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--ratio')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--profile')
    group.add_argument('--no-profile', action='store_true')
    args = parser.parse_args()
    try:
        result = finalize(args.input.read_text(encoding='utf-8-sig'), profile=args.profile,
                          no_profile=args.no_profile, ratio=args.ratio)
    except (OSError, ValueError) as error:
        parser.error(str(error))
    if args.output:
        args.output.write_text(result + '\n', encoding='utf-8')
    else:
        print(result)


if __name__ == '__main__':
    main()
