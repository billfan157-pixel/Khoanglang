# Khoảng Lặng 02:17 — open questions against story canon v3

Recorded, not resolved. Nothing here has been "fixed" in the implementation;
where Milestone 1 had to assume something, it says so.

## A. Full source now present

`docs/story/Khoang_Lang_02_17_Cot_truyen_v3.md` is the complete 1,132-line V3
updated on 30/09/2026, including §§8–14. It was copied byte-for-byte from the
user-supplied file without editing the story text. The earlier complete 972-line
version is preserved as `Khoang_Lang_02_17_Cot_truyen_v3_full_2026-09-29.md`;
the still earlier 435-line project copy remains as
`Khoang_Lang_02_17_Cot_truyen_v3_truncated_2026-09-29.md`.

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
Lệ's father, 65 real victims, 12 nights, Nhi's chosen name is "Vọng", Lệ
travelled with cô Vân's group, the Hùng–Mai silent agreement, T2 masked rather
than deleted, the Luật Neo states, and an 18–22 hour target. The 30/09 update
adds Tuyết as a temporary worker and Bống as her seven-year-old daughter, Long
retaining the wage and rice ledgers, the two cut words in the official bulletin,
and the resonance zone. §3's engineering numbers are explicitly provisional.
These are source assumptions awaiting the developer's confirmation; this file
does not amend them.

## C2. Continuity review after the 30/09 update

* **Resolved by source:** §3 distinguishes the nightly broadcast, the masked
  archive copy used in Hồi 3–5, and the untouched T2 original retrieved in
  Hồi 6. Only the original yields all 65 voices.
* **Resolved by source:** Ending B preserves only the Trạm trung tâm line and
  its connection to hầm B and Quảng trường; the four earlier cuts remain.
  §12 now specifies construction status for each of the six ending branches.
* **Minor wording still to reconcile:** §12's general “Giữ kín” cost says the
  bulletin still plays and people remain overwritten, while the six-state
  matrix says A/Giữ kín has no loudspeaker and C/Giữ kín uses a new bulletin.
  Treat the matrix as the branch-specific description unless the story author
  clarifies otherwise; do not copy the general sentence into every ending.

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
