---
name: kl-story-data
description: Keeps Khoảng Lặng story facts consistent by storing them as data (data/story/*.json) and validating clue seeding, source independence, and who-knows-what with a script that runs outside Unreal. Also defines the protocol for deviating from canon (prototype_only flags, decision records). Use this skill whenever you add or change a clue, recording, source, puzzle, NPC knowledge, dialogue that states a story fact, or a chapter reveal; whenever you generate Unreal data assets from story facts; and before finishing any task that touched story content.
---

# Story as data

The story's biggest long-term risk is contradiction: a fact used in chapter 3 that the NPC only learns in chapter 5, or a puzzle that needs a recording the player cannot have yet. Hundreds of small agent edits make that likely. So story facts live in plain JSON files that git can diff and a script can check, and Unreal assets are generated from them.

## Layout

```
data/story/
  truths.json     facts the player eventually learns
  clues.json      things that point toward a truth
  sources.json    recordings and people the player can compare
  puzzles.json    sealing puzzles (sets of sources for a cut sentence)
  knowledge.json  who learns and uses which truth, and when
```

Field definitions: `references/schema.md`. Ids are ASCII `snake_case`; player-facing text goes in separate `text_vi` fields in UTF-8 NFC (see `kl-vietnamese-text`).

Every entry carries a `canon_ref` such as `V3 section 8.2`. No `canon_ref` means invented content: the validator warns, and you should ask the developer before keeping it.

## The validator

```
python .agents/skills/kl-story-data/scripts/validate_story_data.py data/story
python .agents/skills/kl-story-data/scripts/validate_story_data.py data/story --release
```

It checks, and exits 1 on any error:

1. Every truth has at least two clues placed at least one chapter before its reveal.
2. Every sealing puzzle has at least two sources, at least one of them `independent`, and no source is unavailable at the puzzle's chapter.
3. Nobody uses a truth in a chapter earlier than the chapter in which they learn it.
4. Ids are unique and every reference points at something that exists; source kinds are `independent`, `related` or `interested`.

`--release` turns every `prototype_only` entry into an error, so scaffolds cannot ship by accident.

The thresholds at the top of the script mirror the V3 rules as summarized in project notes. If V3 says something different, change the constants and say so in a decision record; do not bend the data to fit the script. Self-test the script after editing it: `fixtures/valid` must exit 0 and `fixtures/invalid` must exit 1 (the fixtures are synthetic and contain no canon).

## Workflow for a story change

1. Find the governing canon section. If none exists, stop and ask.
2. Edit the JSON (or add entries), with `canon_ref`.
3. Run the validator; fix errors at the data, not by loosening the rule.
4. Regenerate the Unreal data assets from the JSON with the project's generator (idempotent, with the overwrite guard from `kl-repo-hygiene`), then verify counts match the JSON.
5. Report what changed in story terms, in a few lines.

## Deviating from canon

Sometimes a prototype needs something the canon does not provide, such as an independent source in the school during Hồi 1 when the only independent recording is not obtainable until Hồi 4.

1. Choose the smallest reversible option, or ask the developer if several are plausible.
2. Mark every affected entry `"prototype_only": true`.
3. Write `docs/decisions/D###-short-name.md`: the problem, the canon section, the choice, why, and what must be revisited and by which gate.
4. Never edit the canon file to match the implementation.

## Dialogue and text that states facts

A line that reveals or relies on a truth counts as a use. Register it in `knowledge.json` (`uses`) so the validator can catch a character who knows too much too early.
