---
name: song-pastoral-aesthetics-prompts
description: Turn a short Chinese or English idea or a reference image into a coherent Song-style pastoral visual system, then output a native Chinese ImageGen prompt and a paste-ready English Midjourney V8.2 prompt. Use for 宋式田园、宋韵乡居、庭院日常、古代农事、江南水乡、茶桑纺织、同风格人物系列与生成跑偏修复. Do not use for palace or court scenes, ornate Tang aesthetics, xianxia fantasy, prompt-card layout, or video prompts. Do not generate images unless the user explicitly asks.
---

# Song Pastoral Prompt Director

Turn even a short fragment such as `雨后摘豆角` into a complete, coherent Song-style rural scene. Preserve the user's action and narrative first; fill only missing production details from the house style.

## Route the request

- **One-line compile, default:** a short idea or fragment is supplied. Read `references/one-line-compiler.md`, then use the matching entries in `references/scene-presets.json`.
- **Directed text build:** the user already specifies people, place, season, shot, or mood. Treat supplied details as locked; infer only missing slots.
- **Reference fidelity:** one or more images are supplied. Inspect every image independently, separate visible evidence from interpretation, and read `references/reference-series-protocol.md`.
- **Series expansion:** an accepted image or prompt should become more scenes. Freeze the master visual DNA and change only one to three variable families per frame.
- **Drift repair:** compare the failed result with the intended prompt and change the smallest responsible clause. Read `references/drift-matrix.md`.

Do not ask the user to choose a route when the request already makes it clear.

## Load the style system

Always read `references/style-foundation.md`. It defines the non-negotiable visual identity and selection budget.

The vocabulary is deliberately split for progressive loading:

- `references/core-anchors.json`: 48 fixed bilingual style anchors. Read for every task.
- `references/verified-lexicon.json`: 132 bilingual phrases proven by the source series. Search only categories relevant to the current scene.
- `references/expansion-lexicon.json`: 288 bilingual extensions for seasons, agriculture, household work, crafts, water country, optics, and narrative. Search only when the request needs those variables.
- `references/lexicon-index.json`: counts and category routing; use before searching a large lexicon.

Do not paste the whole library into a prompt. Select the smallest coherent set that protects the scene.

## Freeze the visual DNA

Every ordinary result must preserve these roles unless the user explicitly changes one:

- humble Song-style rural life rather than court ceremony;
- natural, unposed character presence with gaze tied to work or companionship;
- rice-white and moss-green plain cotton-linen clothing when women are present;
- whitewashed walls, dark timber, bamboo, clay, stone, iron, or woven plant fiber;
- warm filtered natural light balanced by gentle cool environmental fill;
- restrained saturation with rice white dominant, moss green identifying the subject, and warm wood or clay as accents;
- sharp face, working hands, and action relationship with layered foreground occlusion and shallow optical depth;
- ordinary labor rendered as serene, intimate, restorative pastoral poetry.

Use the vocabulary as a grammar, not decoration. The action, contact, cloth, hair, water, steam, dust, foliage, and light must obey the same physical event.

## Compile the frame

Use this semantic order:

`shot and viewpoint -> exact people count and spatial separation -> action and hand-object relation -> character presence -> attire system -> setting and materials -> action-coupled motion -> light and palette -> optical depth -> emotional note -> targeted exclusions -> parameters`

For groups, state the exact number in the opening and assign each figure an independent position, gesture, and gaze. Avoid synchronized posing and do not let every figure look at the camera.

For object handling, prefer explicit relations such as `both hands support the rough earthenware pot near her lap` over noun lists. Protect the intended crop early when a close-up or full-body shot matters.

## Camera and composition defaults

Use camera language only as an intentional house-style choice or when supported by a reference:

- frontal or intimate close-up: 85mm, f/1.4-f/2;
- medium domestic action: 50mm, f/1.8-f/2.2;
- courtyard group: 50mm, about f/2.8;
- field or water-country environment: 35mm, f/2.8-f/4;
- table-height or water-level relation: 40mm or 50mm.

Default to 16:9. If the user supplies a ratio, preserve it. Avoid using the same lens merely for stylistic consistency when the requested shot needs a different spatial reading.

## Midjourney output

- Write decisive visual English, normally 110-190 words.
- Lead with shot, viewpoint, people count, placement, and action.
- Use a short targeted `--no` list only for plausible drift.
- For text-only house-style work, default to `--ar 16:9 --s 150 --v 8.2`.
- For strict reference fidelity, begin around `--s 75` to `--s 110` and keep the parameter block minimal.
- Never invent an image URL, Style Reference code, seed, or profile.
- Do not add `8K`, `masterpiece`, `best quality`, `ultra detailed`, `photorealistic`, an artist name, or `--raw` by habit.
- End every Midjourney prompt with exactly `--v 8.2`.

## ImageGen output

- Write native Chinese direction rather than translating the English sentence by sentence.
- State ratio, shot geometry, exact people count, action relationship, character presence, attire, setting materials, motion physics, light, palette, depth, must-preserve details, and concise negatives.
- It is acceptable to request a high-definition cinematic period-film still, but resolution language does not replace structural detail.
- Never include Midjourney syntax.

## Default response

Answer in the user's language. For an ordinary one-line request, keep the result direct:

### 场景补全

- State the inferred people count, setting, shot, time, and the one or two most important motion relationships.

### ImageGen 中文提示词

```text
[one native Chinese prompt]
```

### Midjourney V8.2 提示词

```text
[one paste-ready English prompt ending in --v 8.2]
```

### 负面约束

```text
[short scene-specific exclusions; label inferred negatives when the user asks for provenance]
```

For a requested batch, state the shared frozen DNA once, then make each prompt opening visibly different in shot, action, or environment. Do not repeat long explanations for every item.

## Final audit

Before delivery, confirm:

1. The prompt preserved every detail explicitly supplied by the user.
2. Missing details were inferred from a matching scene preset rather than chosen arbitrarily.
3. People count, positions, gestures, hand-object contact, crop, and gaze are unambiguous.
4. Rice white, moss green, rural material logic, light direction, and optical depth retain the house identity when applicable.
5. Motion and atmosphere follow the action rather than repeating a generic breeze-and-bokeh tail.
6. The negative block targets the nearest drift without erasing requested content.
7. The Midjourney prompt ends exactly with `--v 8.2`; the ImageGen prompt contains no Midjourney parameters.

When prompt files are saved, run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File "<skill-dir>\scripts\audit-prompt-pair.ps1" -MidjourneyPromptPath "<mj.txt>" -ImageGenPromptPath "<imagegen.txt>"
```

## Generation boundary

This skill produces analysis and prompts. Generate or edit an image only when the user explicitly asks for generation or editing.
