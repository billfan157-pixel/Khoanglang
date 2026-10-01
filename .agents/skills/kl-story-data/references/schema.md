# Story data schema

All files are UTF-8 (NFC) JSON. Ids are ASCII `snake_case`, unique within their file. `chapter` and
`reveal_chapter` are integers (Hồi 1 = 1, and so on). Examples below are synthetic, not canon.

## truths.json - array

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | Stable id, never reused |
| `reveal_chapter` | int | yes | Chapter in which the player is told or shown this truth |
| `summary` | string | no | One-line English note for developers |
| `text_vi` | string | no | Player-facing wording, if the truth is shown verbatim |
| `canon_ref` | string | recommended | Canon section, for example `V3 section 9` |
| `prototype_only` | bool | no | Scaffold that must be revisited (see `kl-story-data/SKILL.md`) |

## clues.json - array

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | |
| `truth` | string | yes | Id in truths.json |
| `chapter` | int | yes | First chapter in which the player can encounter the clue |
| `where` | string | no | Place or object, for level building |
| `text_vi` | string | no | Player-facing text |
| `canon_ref`, `prototype_only` | | | As above |

Seeding rule (validator): each truth needs `MIN_CLUES_BEFORE_REVEAL` clues whose `chapter` is at
least `CLUE_LEAD_CHAPTERS` earlier than the truth's `reveal_chapter`.

## sources.json - array

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | |
| `kind` | string | yes | `independent`, `related` or `interested` (Độc lập / Có liên quan / Có lợi ích) |
| `chapter_available` | int | yes | First chapter in which the player can use this source |
| `medium` | string | no | `recording`, `person`, `document`, ... (a living person counts as a source) |
| `canon_ref`, `prototype_only` | | | As above |

## puzzles.json - array

| Field | Type | Required | Meaning |
| --- | --- | --- | --- |
| `id` | string | yes | |
| `chapter` | int | yes | Chapter in which the puzzle is played |
| `sources` | array of source ids | yes | Sources the player compares to seal the sentence |
| `truth` | string | no | Truth the sealed sentence supports |
| `canon_ref`, `prototype_only` | | | As above |

Sealing rule (validator): at least `MIN_SOURCES_PER_PUZZLE` sources, at least one `independent`,
and every source available by the puzzle's chapter.

## knowledge.json - object

```json
{
  "learns": [{"npc": "synthetic_npc", "truth": "synthetic_truth_a", "chapter": 2}],
  "uses":   [{"npc": "synthetic_npc", "truth": "synthetic_truth_a", "chapter": 3, "ref": "scene or dialogue id"}]
}
```

Rule (validator): an entry in `uses` needs a `learns` entry for the same npc and truth in the same
or an earlier chapter.

## Adding fields

Add optional fields freely. Adding a required field, changing a rule, or renaming a file means
updating `validate_story_data.py`, its fixtures, and this document together.
