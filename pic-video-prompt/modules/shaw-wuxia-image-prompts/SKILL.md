---
name: shaw-wuxia-image-prompts
description: Turn one Chinese or English sentence, a Shaw wuxia substyle, or reference images into coherent Midjourney V8.2 English prompts and native Chinese ImageGen prompts. Use for 邵氏电影风、邵氏武侠、孤独剑客、七十年代棚拍武侠、人工山水武侠、邵氏动作武侠、同风格组图和生成跑偏修复. Do not use for video prompts, prompt-card layout, or automatic image generation unless the user explicitly requests generation.
---

# Shaw Wuxia Image Prompt Director

Turn the user's shortest useful idea into one committed Shaw-wuxia still-image direction. Inherit the routing, cinematic-DNA discipline, and native Midjourney/ImageGen compilation logic of a cinematic prompt director, but use the specialized style system in this Skill rather than a generic film-style lookup.

## Route the request

Choose the smallest route that fits. Do not ask the user to select a mode when the default below is safe.

- **One-line build:** one scene or subject becomes one matched prompt pair.
- **Series build:** 一组、系列、组图 or multiple images freezes one shared Shaw DNA and varies shot function, action, environment interaction, or wardrobe.
- **Reference reverse:** inspect every supplied image independently, assign roles, then preserve its approved traits.
- **Prompt enhance:** retain the user's subject and chosen branch while improving hierarchy and target-model syntax.
- **Drift repair:** compare the generated candidate with its source prompt or approved image and correct the smallest responsible clause.

This Skill produces still-image prompts. It does not produce timelines, dialogue, sound, camera motion, prompt cards, or images unless the user explicitly requests those deliverables.

## Resolve the Shaw branch

Read [references/shaw-style-system.md](references/shaw-style-system.md) before writing prompts.

- Default to `modern-lone-wuxia` when the user says only 邵氏电影风、邵氏孤侠、孤独剑客, or supplies a quiet travel scene.
- Use `studio-classic` for 老邵氏、六七十年代、棚拍、人工山水、绘景、古龙式唯美空间, or explicit theatrical-set language.
- Use `action-wuxia` for 对决、围攻、打斗、招式、阳刚武侠, or action-first requests.
- If the user names a Shaw director, keep the name at most once and translate it into visible mechanisms. Do not rely on the name alone or claim that a broad Shaw label is one uniform historical style.

## Useful defaults

- One image -> one prompt pair.
- 一组 / series without a count -> four frames.
- Default ratio -> `16:9`; obey an explicit ratio.
- Default branch -> `modern-lone-wuxia`.
- If only the style is supplied, infer one restrained wandering-swordsman narrative seed and state the assumption in one sentence.
- Generate no images unless explicitly requested.

## Build the shared DNA

For `modern-lone-wuxia`, read [references/lone-wuxia-dna.md](references/lone-wuxia-dna.md). Freeze only the anchors that make the set recognizable:

- one visual thesis and dominant figure-to-space relationship;
- character or subject presence without overloading identity details;
- composition grammar, subject scale, and negative-space behavior;
- costume/material family and any weapon attachment relation;
- light direction, palette roles, and optical treatment;
- emotional tension, must-keep anchors, and allowed variables.

For a series, assign each frame a distinct job such as establishing world, human gesture, threshold/crossing, identity close-up, or environmental echo. Change one to three variable families per frame. Couple action to plausible fabric, reeds, rain, water, dust, reflection, and light behavior.

## Compile for each model

Read [references/platform-compilers.md](references/platform-compilers.md) before final output.

Midjourney attention order:

`shot geometry and dominant relation -> subject count, scale, position, and action -> costume/weapon relation -> environment layers -> motion physics -> light, palette, and optical behavior -> one Shaw branch summary -> nearest drift constraints -> parameters`

ImageGen attention order:

`ratio and frame geometry -> subject count/scale/position -> decisive relations -> branch mechanisms -> material and motion -> light/palette/optics -> must keep -> allowed change -> concise negatives`

Every Midjourney prompt must be paste-ready English, include the intended `--ar`, and end exactly with `--v 8.2`. ImageGen prompts must be native Chinese direction and contain no Midjourney syntax.

## Default response

Respond in the user's language.

### 创意设定

One sentence stating the narrative seed, selected branch, and visual thesis.

### 共享邵氏电影 DNA

A compact set of distinctive anchors. State the branch explicitly.

### 镜头 01 — [short title]

- **画面职责：** one short phrase.
- **构图思路：** subject scale, position, foreground weight, and negative space.

#### Midjourney V8.2

```text
[paste-ready English prompt ending in --v 8.2]
```

#### ImageGen 中文提示词

```text
[native Chinese prompt]
```

#### 负面约束

```text
[only the nearest plausible drift]
```

Repeat the frame section for the requested count. Do not shorten or merge prompt text unless the user asks.

## Reference and repair rules

For supplied images or failed generations, read [references/reference-and-drift-repair.md](references/reference-and-drift-repair.md).

- Inspect every image independently; do not infer inspection from filenames or thumbnails.
- The user's approved role assignment is authoritative.
- Treat a failed candidate as a negative example unless the user approves one of its traits.
- Protect passing anchors and repair only the smallest failed clause.
- Text alone cannot guarantee strict reconstruction. Explain Image Prompt versus Style Reference roles when this materially improves fidelity; never invent URLs, codes, profiles, or seeds.

## Audits

For three or more frames, reference synthesis, or drift repair, save a temporary manifest using [references/prompt-set-schema.md](references/prompt-set-schema.md), then run:

```powershell
python scripts/audit_shaw_prompt_set.py path\to\prompt-set.json
```

Use the branch lookup when the request contains an alias or when a test needs the canonical branch record:

```powershell
python scripts/style_profile.py "邵氏孤侠"
```

Audit success proves structure and prompt-pair contracts, not beauty or visual fidelity. Manually confirm subject scale, count, weapon count, branch mechanisms, and the prompt opening.

## Boundaries

- Do not reduce the style to `Shaw Brothers style` or `Hong Kong kung-fu film`; concrete mechanisms must carry the prompt.
- Do not make every Shaw request a misty lone-swordsman scene. The default branch applies only when the request is quiet or underspecified.
- In wide modern-lone-wuxia frames, prevent automatic center bias, oversized subjects, duplicate weapons, extra companions, fantasy portals, and commercial costume-poster lighting.
- Do not add generic quality tails, cameras, lenses, exact film stocks, `masterpiece`, `8K`, `photorealistic`, `hyperrealistic`, or `--raw` without evidence or user intent.
- Do not recreate a specific identifiable film frame without a supplied reference.

