"""Audit explicit prompt contracts, not generated image quality. Standard library only."""
import argparse
import json
import re
from pathlib import Path


def flags(prompt):
    matches = list(re.finditer(r"(?<!\S)--([a-z][a-z0-9-]*)\b", prompt))
    result = {}
    for i, match in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(prompt)
        result.setdefault(match.group(1), []).append(prompt[match.end():end].strip())
    return result


def audit(data):
    errors, warnings = [], []
    if not isinstance(data, dict) or not isinstance(data.get('items'), list) or not data['items']:
        return {'valid': False, 'errors': ['items must be a nonempty list'], 'warnings': []}
    items = data['items']
    expected = data.get('expected_count')
    if type(expected) is not int or expected != len(items):
        errors.append('expected_count must be an integer matching the number of items')
    seen = set()
    for index, item in enumerate(items, 1):
        tag = f'item {index}'
        if not isinstance(item, dict):
            errors.append(f'{tag}: must be an object')
            continue
        required = ('id', 'request', 'scene_type', 'ratio', 'composition_zh', 'mj_prompt',
                    'imagegen_prompt', 'negative_zh', 'negative_en', 'profile_mode')
        missing = [key for key in required if not isinstance(item.get(key), str) or not item[key].strip()]
        if missing:
            errors.append(f'{tag}: missing text fields: {", ".join(missing)}')
            continue
        tag = item['id']
        if tag in seen:
            errors.append(f'{tag}: duplicate id')
        seen.add(tag)
        count = item.get('subject_count')
        if type(count) is not int or count < 0:
            errors.append(f'{tag}: subject_count must be a nonnegative integer')
        scene = item['scene_type']
        if scene in ('duel', 'unarmed', 'standoff') and count != 2:
            errors.append(f'{tag}: this scene_type requires two people')
        if scene == 'empty' and count != 0:
            errors.append(f'{tag}: empty scene must have zero people')
        ratio = item['ratio']
        if not re.fullmatch(r'[1-9]\d*:[1-9]\d*', ratio):
            errors.append(f'{tag}: invalid ratio')
        prompt = item['mj_prompt'].strip()
        if not prompt.endswith('--v 8.2'):
            errors.append(f'{tag}: MJ must end with --v 8.2')
        params = flags(prompt)
        for key, values in params.items():
            if len(values) != 1:
                errors.append(f'{tag}: duplicate --{key}')
        if params.get('ar') != [ratio]:
            errors.append(f'{tag}: MJ ratio does not match contract')
        if params.get('v') != ['8.2']:
            errors.append(f'{tag}: version mismatch')
        cn = item['imagegen_prompt']
        if re.search(r'--[a-zA-Z]', cn):
            errors.append(f'{tag}: ImageGen contains MJ flags')
        if ratio not in cn or not re.search(r'[\u4e00-\u9fff]', cn):
            errors.append(f'{tag}: ImageGen must be Chinese and state the ratio')
        profile_mode = item['profile_mode']
        if profile_mode not in ('portable', 'source', 'user'):
            errors.append(f'{tag}: unsupported profile_mode')
        if profile_mode == 'portable' and 'profile' in params:
            errors.append(f'{tag}: portable mode must not silently add a profile')
        if profile_mode in ('source', 'user'):
            value = 'z4yrncu' if profile_mode == 'source' else item.get('profile_value')
            if not value or params.get('profile') != [value]:
                errors.append(f'{tag}: profile does not match declared source/user value')
            if not item.get('profile_authorization'):
                errors.append(f'{tag}: profile requires an explicit authorization record')
        negative = params.get('no', [''])[0]
        terms = [term.strip().lower() for term in negative.split(',')]
        if type(count) is int and count > 0 and any(t in ('people', 'person', 'humans', 'human', '人物', '人') for t in terms):
            errors.append(f'{tag}: --no excludes the requested people')
        if any(t in ('blur', 'motion blur') for t in terms):
            warnings.append(f'{tag}: blanket blur exclusion may conflict with photographic motion/depth')
        for key in ('sref', 'seed', 'hd', 'raw', 'chaos', 's', 'stylize'):
            if key in params and not item.get('parameter_authorization'):
                warnings.append(f'{tag}: check authorization/provenance for --{key}')
        if re.search(r'<[^>]+>|\[(?:IMAGE|URL|PROFILE)', prompt, re.I):
            errors.append(f'{tag}: unresolved placeholder in pasteable prompt')
    return {
        'valid': not errors, 'item_count': len(items), 'errors': errors, 'warnings': warnings,
        'scope': 'Text structure and explicit parameter contracts only; no image generation or visual fidelity proof.'
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--report', type=Path)
    args = parser.parse_args()
    try:
        result = audit(json.loads(args.input.read_text(encoding='utf-8-sig')))
    except (OSError, ValueError) as exc:
        result = {'valid': False, 'errors': [str(exc)], 'warnings': []}
    output = json.dumps(result, ensure_ascii=False, indent=2)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(output + '\n', encoding='utf-8')
    print(output)
    return 0 if result['valid'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
