# Khoảng Lặng 02:17 — Milestone 1 technical notes

Short record of what was built, the decisions behind it, and what is still open.
Story canon lives in `docs/story/Khoang_Lang_02_17_Cot_truyen_v3.md`; open story
questions live in `docs/story/OPEN_QUESTIONS_V3.md`.

## 1. What Milestone 1 is

A 5–10 minute investigation slice inside **Trường tiểu học số 3** (the school
that was the flood-night muster point in 2002, canon §5). The loop:

1. Walk the hall, find the class roster note and the attendance book in room 3.
2. Take the attendance book (document evidence).
3. Find the hall PA head + tape deck at the north end, play the 02:16:34 tape.
4. Press **Q** for **NGHE LỌC** — the masked broadcast becomes intelligible and
   the 65 answers separate out.
5. Open the journal (**Tab**), corroborate two independent sources, see that
   63 written names and 65 spoken answers do not match.
6. Return to room 3, hold NGHE LỌC, look into the far corner: the seated figure
   becomes visible. Press **E**: the roll call answers, the corner light turns
   red, the ending card appears.

## 2. Architecture

```
BP_KL_EvidenceDef (PrimaryDataAsset)      data-driven evidence record
  EVD_SoDiemDanh / EVD_Bang021634        the two Milestone 1 evidence items

BP_KL_InvestigationComponent   STATE     evidence array, quest flags, objectives,
                                         prompt/subtitle text, journal content
BP_KL_ListeningComponent       PRESENTATION  the two listening states (audio only)
BP_KL_InteractComponent        BEHAVIOUR  one reusable interaction payload
  BP_KL_Prop_AttBook           document / collect
  BP_KL_Prop_TapeDeck          audio recording / collect + play
  BP_KL_Prop_Roster            environmental read
  BP_KL_Prop_Corner             the supernatural beat

BP_FirstPersonCharacter (template, extended in place)
  InitKL / UpdateFocus / PollKeys / CheckHeard / TickKL
BP_KL_HUD        canvas overlay: objective, prompt, subtitle, journal, ending
BP_KL_GameMode   template game mode + HUD/pawn/PC wiring
Lvl_KL_School3   the graybox
```

Rules the code follows:

* **State and presentation are separate components.** The investigation
  component never touches audio or the canvas; the listening component never
  touches quest flags.
* **One interaction payload for every prop.** `BP_KL_InteractComponent` is
  configured per instance with mode flags (`bTapeMode`, `bCornerMode`,
  `bNoteMode`, default = document). Adding a new interactable means placing an
  actor with that component and setting flags — no new graph code.
* **Evidence content lives in data assets.** Adding evidence is a new
  `BP_KL_EvidenceDef` instance, not new logic.
* **No Blueprint Interface.** Interfaces need a cast node to reach, and this
  editor toolset cannot create casts to Blueprint classes
  (`Utilities|Casting|CastToBP_*` is not in the action database). The component
  class is fetched with `GetComponentByClass` and its functions are called on
  that typed reference instead.

## 3. Decisions worth knowing

**The template character is extended in place.** A Blueprint child does *not*
inherit the parent's Event Graph, so a `BP_KL_Character` child of
`BP_FirstPersonCharacter` would lose all Enhanced Input movement and mouse look
(the template binds them through `UK2Node_EnhancedInputAction` event nodes,
which this toolset cannot create). Extending the template asset is the only way
to keep the template movement. **The template map, materials and animations are
untouched**; only the character BP gained three components and a few functions.

**Input is key polling, not Enhanced Input.** `Q/E/Tab/F/Enter/Esc` are read in
`PollKeys` through `PlayerController:WasInputKeyJustPressed`. WASD, mouse look,
sprint and jump still use the template's Enhanced Input, so there is no
conflict. All prototype input lives in one function (`PollKeys`) precisely so
it can be swapped for Enhanced Input actions later.

**Focus is a proximity sphere, not a gaze trace.** The character runs a
`SphereTraceByChannel` (radius 260 cm) from its own location with
`bIgnoreSelf`, and treats the first hit that owns a `BP_KL_InteractComponent`
as focused. A true view-cone trace would need a scaled forward vector, and this
engine build exposes no vector-by-scalar node. The trade-off is *more* forgiving
than a gaze trace, which suits a first-playable slice.

**Audio differences are real, not labels.** `S_KL_T2_Masked` and
`S_KL_T2_Clear` are two renders of the same 16-second broadcast: masked is
low-passed to 380 Hz under a carrier hiss, clear keeps the band. Both contain 65
answer groups, two of them deliberately tiny, one of them a child voice cut off
mid-sentence. NGHE LỌC also drops the mask bed, raises the clarity tone and the
speaker hum, ducks the ambience to 0.30 and lifts its 700 Hz low-pass. The
figure in the corner is only un-hidden while NGHE LỌC is on and the player is
looking at it.

**Audio assets are original and procedural.** `gen_placeholder_audio.py`
synthesises everything with a small formant/noise DSP kit. There is no recorded
speech anywhere in the project; every spoken line is delivered as on-screen
text, which also satisfies the accessibility requirement.

**Text is stored as numbered lines.** Evidence bodies are `Body1..Body4` and
clues `Clue1..Clue3` rather than one multi-line blob, because the Milestone 1 HUD
draws one canvas row per string and does not wrap text.

## 4. Build tooling

Everything is generated by Python through Epic's `EditorToolset`, so the project
stays diff-able and rebuildable:

```
Content/Python/KhoangLang/
  kl_core.py              shared graph-building library (verified node table)
  build_10_assets.py      audio flags, materials, evidence data
  build_20_blueprints.py  components, character, HUD, game mode
  build_30_level.py       interactable props + the school graybox
  build_40_verify.py      static verification pass
  run_ue_script.ps1       headless runner
  run_playtest.ps1        launches a game session + in-game smoke test
```

Run order: `build_10` → `build_20` → `build_30` → `build_40`. All four are
idempotent; re-running rebuilds in place.

`kl_core.py` hard-codes only node type ids and function paths that were probed
against this exact editor build. `B.audit()` catches the one failure mode that
is invisible while wiring: a component method whose `self` pin is left
unconnected, which compiles in-session but makes the whole Blueprint
`BS_ERROR` the next time it is loaded.

## 5. Known limitations of Milestone 1

* `BP_KL_InvestigationComponent` holds two evidence slots (`DocDef`, `TapeDef`)
  rather than an arbitrary list with per-entry rendering. The `Collected` array
  is already filled, so growing this is a rendering change, not a data change.
* The HUD draws one row per string: no text wrapping, no scrolling, no
  localisation table. A real build wants UMG + a String Table.
* Reveal feedback is the figure appearing plus a corner light. There is no
  post-process, no fade, no audio sting attached to the reveal itself.
* `Esc` quits through `Game|QuitGame`; in-editor PIE may intercept it first.
* Interaction is proximity-based (see above).
* Everything is Blueprint. The evidence/quest component has 55 graphs, which is
  a lot of hand-wiring — this is the strongest argument for a C++ base class in
  Milestone 2.

## 6. Verification status

`build_40_verify.py` checks, headlessly:

* all 12 Blueprints compile with zero errors (and zero unconnected
  component-`self` pins),
* the evidence Data Assets really are `BP_KL_EvidenceDef_C`,
* all 12 sound waves and all 11 materials resolve,
* every prop carries the interact component with the intended flags,
* `Lvl_KL_School3` loads with 75 actors, exactly one of each prop, one
  `PlayerStart`, 9 lights, and `BP_KL_GameMode` as the default game mode.

Not yet verified on this machine: Play-In-Editor / a real game session, input
response, the listening-state mix, and the scripted beat. See the milestone
report for the reason and for the exact manual test list.
