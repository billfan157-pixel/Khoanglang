# Review queue

No release candidate is ready for acceptance.

- Story: the user's 30/09 V3 update is now the authoritative source, with
  1,132 lines and sections 1–14. Review its explicit unconfirmed assumptions
  and the remaining items in ../story/OPEN_QUESTIONS_V3.md before dependent scenes.
- Quality bar: review QUALITY_BAR.md before judging G1: worn Vietnamese school,
  restrained practical lighting, captions, provisional 720p/30 fps target.
  Proceed on this reversible proposal unless objected.
- G0_graybox_pie_hud.png is an inspected HUD-overlap failure baseline.
- Source audio engineering baseline: G1_source_audio_measurements.json and
  G1_T2_source_spectrum.csv measure 12 placeholder files; sample RMS is not LUFS,
  and this is not the in-game mix. Final voice performances remain missing.
- Listen to source S_KL_T2_Masked.wav 0-16s, then S_KL_T2_Clear.wav 0-16s:
  does the separation suggest different listening states without an excessive
  level jump? Listen to S_KL_RollCall.wav 0-13s followed by S_KL_ChildReply.wav
  0-3.2s: review cadence only; these synthesized tones contain no real words.
  Queue in-game beat acceptance only after the production PIE is captured.
- Final acceptance: HUMAN_SIGNOFF.md must be authored by the user, not an agent.

## 2026-09-30 G1 Development build review (not RC)

Build: _release_work/20260930_214738_28dac5b5/WindowsBuild; pre-launch artifact
SHA256 8943b0d4065fe8600b151c7e1a867a542d4523c297d7c6d32d56b286ae32effb.
The real game launched; physical-input review stopped by the user's Escape.
Do not interpret that stop as audio/art approval or game completion.

- Scene: school entrance, flashlight on/off. Clipping and crushed shadows are
  observed failures; inspect a repaired candidate before judging school identity.
- Scene: enable echo with Q and listen 0–13s roll, 13–16.2s child response.
  Critical captions describe Vietnamese words but source audio is synthesized
  tones: final dialogue/performance missing. Review cadence only on this build.
- Scene: compare three preview criteria, then hold/timed seal for 4s.
  Does noise communicate attention consequences without implying a truth oracle?
- Scene: wrong response and contact false silence. After a repaired candidate,
  judge whether displacement and surviving evidence make the loss understandable.
- Scene: correct two-person response versus the ledger true-name fixture.
  Does the distinction between Giữ and Yên read clearly? Fixture is not Hồi 1.

## 2026-09-30 measured candidate failures

G1_PACKAGED_BASELINE.json binds the same artifact to 1800 actual frame samples:
p95 44.78ms misses the provisional budget. Runtime ShaderMap errors and exit
777003 fail acceptance. The inspected 720p capture has no school geometry;
1080p has geometry, clipped highlights and the unbuilt-light warning.
Do not treat either as proof of full Vietnamese layout/control qualification.

Saved dynamic-light candidate images G1_dynamic_v3_ev-1p5_hall_off.png,
classroom_on.png and deck_on.png were inspected: floor edges and furniture read
better, but the cassette lacks a mount and actor models are placeholders.
Human mood/art review belongs on a later repaired, stable Windows candidate.
# Current atomic checkpoint (2026-10-01)

G1_CHECKPOINT.md and the checkpoint build/runtime reports describe the current
repair scope. This does not request or imply G1/full-game acceptance.
Inspect G1_checkpoint_final_ev-1p5_deck_on.png, deck_side_off.png and
classroom_on.png: cassette support/cap spikes improved; unlit shadows remain
deep, flashlight response bright and HUD contrast weak over pale furniture.
Review the source art and these exact views before visual acceptance.
No new Vietnamese performances were produced. Editor engineering used
-nosound; physical controls and scare effectiveness remain unqualified.
HUMAN_SIGNOFF.md stays user-owned and untouched.
