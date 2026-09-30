# Khoảng Lặng 02:17 — open questions against story canon v3

Recorded, not resolved. Nothing here has been "fixed" in the implementation;
where Milestone 1 had to assume something, it says so.

## A. Full source now present

`docs/story/Khoang_Lang_02_17_Cot_truyen_v3.md` is the complete 972-line V3,
including §§8–14. It was copied from the user-supplied file on 2026-09-30
without editing the story text. The earlier 435-line project copy is preserved
as `Khoang_Lang_02_17_Cot_truyen_v3_truncated_2026-09-29.md`.

Milestone 1 predates this correction. Its NGHE LỌC filter is a listening state;
it does not implement §8.2's Thử nghe → Niêm phong mechanic or §8.5's four
attention tiers. V3 has **three** Nhi states (§8.4) and **three** primary endings
with two truth branches (§12).

## B. Head-count arithmetic in the full V3

The full §3 table is internally consistent. After bà Mai is crossed out, the
valid register contains 61 villagers + cô Vân + ông Đạt + Lệ = **64** names.
Lệ then leaves, yielding **63** names on the memorial wall. Chị Tuyết and bé
Bống are outside the register, so **65** people die and answer the roll call.
Cô Vân's separate “63 + 2” notebook count is her own group (61 villagers,
bà Mai, Lệ) plus the two unnamed people; its 63 is intentionally a different
set from the memorial wall's 63. Do not conflate the two in dialogue or UI.

## C. V3's own "assumptions needing confirmation"

§1 ends with a list of things v3 decided on its own: bà Mai alive, ông Đạt is
Lệ's father, 65 real victims, 12 nights, Nhi's real name is "Vọng", Lệ
travelled with cô Vân's group, the Hùng–Mai silent agreement, T2 masked rather
than deleted, the Luật Neo states, and an 18–22 hour target. All are treated as
canon here because the bible states them, but they are the developer's to
confirm.

## C2. Continuity decisions before dependent scenes

* Hồi 5 says Khải restores the entire 43-second T2 original and hears Nhi's
  complete answer. Hồi 6 says he and Hà first retrieve the T1/T2 originals
  from the sealed archive; §8.2 also puts recovery of the two quietest voices
  from T2 original in Hồi 6. The source and timing of Hồi 5's restoration
  need a deliberate decision.
* Ending B says keeping the network means no entity can Tràn. Four routes
  have already been cut in Hồi 2, 3, 5 and 6. The intended condition of the
  surviving network needs clarification.
* The general “Giữ kín” cost in §12 says the official broadcast continues,
  while A/Giữ kín says there are no loudspeakers. Specify this consequence
  for each ending branch.

## D. Not yet modelled anywhere

* Thời khung 12 đêm (§2) — the prototype has no clock, no night counter, no
  cut schedule. Only a single authored beat exists.
* Sự chú ý bốn bậc (§8) — the prototype has binary attention, not four tiers.
* Nghe cho hết câu / Thử nghe / Niêm phong (§8) — **not implemented at all.**
  Milestone 1's "NGHE LỌC" is a listening state, not the quote-completion
  mechanic. These are different systems with a similar name and must not be
  conflated; the prototype deliberately leaves room for both.
* Luật Neo, trạng thái Tràn / Giữ / Yên (§6) — nothing implemented.
* The two "loops" of §5: which Khe Lạc speaker line is cut, and what happens
  to Người Chờ Điểm Danh after the school line is cut (night 9). The
  prototype's figure stays in the classroom and is never resolved.

## E. Prototype placeholders (non-canonical, labelled)

* The room is labelled "lớp 3" and carries a class roster with two blank
  pencil lines and "ghi sau". Canon states the two blank lines belong to the
  **hầm B** register, not a classroom board. The classroom version is an
  environmental echo, not a claim about canon.
* The 63 names are never listed anywhere in the prototype; only the counts are.
* The corner figure is a plain untextured shape. It is not a model of Nhi and
  carries no name.
* `S_KL_*` audio is formant-synthesised placeholder texture. Real recorded
  dialogue, or a properly voiced pass, is still required.
