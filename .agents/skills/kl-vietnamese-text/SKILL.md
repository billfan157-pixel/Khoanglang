---
name: kl-vietnamese-text
description: Rules and a checker for handling Vietnamese text (diacritics, UTF-8, Unicode NFC) across the Khoảng Lặng pipeline - story documents, JSON data, Python and PowerShell scripts on Windows, and Unreal UI text and fonts. Use this skill whenever you write, edit, generate, move, or display any Vietnamese text, including HUD strings, dialogue, subtitles, story data, documentation, and script output, and whenever you see garbled characters such as "háº¿t" or "Ä‘".
---

# Vietnamese text

Vietnamese carries meaning in stacked diacritics (ế, ợ, ữ, ặ) and in the letter đ. A wrong encoding does not fail loudly; it quietly corrupts player-facing text and then spreads through generated assets. Windows tools default to legacy code pages, which is where most of the damage starts.

## Rules

1. UTF-8 everywhere, normalized to Unicode NFC (precomposed characters). A decomposed "e" + combining mark looks identical but compares unequal and may render wrongly in fonts. Normalize text you receive from copy-paste, speech tools, or translation.
2. Identifiers are ASCII: asset names, file names, JSON keys, ids, folder names, variable and function names. Vietnamese appears only in text values and documents.
3. Keep player-facing text separate from logic: `text_vi` fields in data (see `kl-story-data`), never string literals scattered through graphs.
4. Python on Windows: open files with `encoding="utf-8"`, write JSON with `ensure_ascii=False`, and run scripts with `PYTHONUTF8=1` (or `python -X utf8`). Reading or writing with the default code page produces mojibake.
5. PowerShell: set `[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()` for console output, and use `-Encoding utf8` when writing files. Be aware that older Windows PowerShell may add a byte-order mark; the checker warns about it, and JSON parsers can choke on it.
6. Do not use ASCII-folding, case-insensitive compare, or sorting that ignores diacritics on player text. `đ` is a separate letter from `d`.
7. In Unreal, keep text as localizable text (String Tables) rather than baked into graphs, so wording can change without opening a Blueprint. Whether a given font covers Vietnamese must be confirmed with the developer, because you cannot see the rendering: the font needs Latin-1, Latin Extended-A (ă, đ, ĩ, ũ), Latin Extended-B (ơ, ư) and Latin Extended Additional (U+1EA0 to U+1EF9, the stacked-diacritic letters).
8. Use a fixed stress string when asking a human to check rendering: `Nghe cho hết câu. Đường ướm ợ, ữ, ặ, ỳ, ỷ, ỹ, Ự, Ở.`

## Check before you finish

Run on every directory you touched:

```
python .agents/skills/kl-vietnamese-text/scripts/check_vietnamese_text.py docs data tools
```

It reports `NOT_UTF8`, `MOJIBAKE`, `NOT_NFC`, and `BOM` (a warning). Exit 1 means problems. It skips `.agents/` (these skill files quote mojibake on purpose), `Content/`, `Saved/`, `Intermediate/`, `Binaries/` and `DerivedDataCache/`. If it reports mojibake, find the step that wrote the file with the wrong code page and fix that step; do not hand-patch the output.

## Repairing text

- Mojibake from UTF-8 decoded as Windows-1252 or Latin-1 can sometimes be reversed: `text.encode("cp1252").decode("utf-8")` (or `"latin-1"` for the second case). It only works if no character was lost: Windows-1252 has five undefined bytes, and one of them appears in the UTF-8 of `Đ`, so text containing it may already contain `\ufffd` and be unrecoverable. Try it on a copy and check the result by eye; if it fails or the original is lost, ask the developer for the source text rather than guessing words.
- To normalize: `unicodedata.normalize("NFC", text)`.
- Never "fix" Vietnamese wording yourself in canon or data without a request. Spelling, tone marks and word choice are authored content.

## When you cannot check rendering

You cannot see the HUD. After changing UI text or fonts, put `[HUMAN-NEEDED]` on the rendering claim and ask the developer to look at the stress string in the running game (`kl-verification`).
