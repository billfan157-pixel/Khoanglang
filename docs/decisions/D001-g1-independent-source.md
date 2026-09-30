# D001 — G1 independent source is a prototype scaffold, not canon

Date: 2026-09-30. Decided by the project owner during G1 preflight.

## Decision

For the G1 classroom loop only, the "at least two sources, one of them
independent" rule (V3 §8.2 step 2) is satisfied with these three source
entries, all flagged `prototype_only = true`:

| Source | Label (V3 §8.3) | Note |
| --- | --- | --- |
| thầy Lâm, living testimony in the school | **Độc lập** | Independent person source |
| T2, masked broadcast copy | **Có liên quan** | Related |
| Attendance book (sổ điểm danh) | **Có lợi ích** | Has an interest |

No canon text was edited. `docs/story/` remains read-only.

## Why this deviates from canon

V3 §3 states T3 (the automatic line recorder in hầm B) is the **only
independent recording**, because nobody in Căn phòng 02:00 knew it existed
until anh Tư found the wiring diagram — and anh Tư supplies that only in
Hồi 4. Hồi 1, in the school, canon has no independent recording available.

Placing thầy Lâm in the school in Hồi 1 also sits awkwardly with V3 §9 and
§10 Hồi 3, which is where thầy Lâm hands over cô Vân's notebook. His presence
at the school in Hồi 1 is a staging convenience, not a canon claim.

## Required follow-up

- Every affected data row carries `prototype_only = true` so the scaffold can
  be found and removed in one pass.
- This must be revisited **before the vertical slice** (V3 §13 step 2). The
  vertical slice is 45–60 minutes of real play, and a wrong independent source
  would teach the player a false rule.
- Do not let this scaffold reach Hồi 3+, where T3 genuinely becomes available.

## Alternatives rejected

- Add a T3 stand-in prop in the classroom: invents an object canon does not
  place in the school, and teaches the player that a recorder is lying around.
- Relax the two-source rule for G1: hides the deviation instead of labelling it.
