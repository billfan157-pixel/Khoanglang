# Production school runtime repair — 2026-09-30

This evidence qualifies the repaired prototype foundation. It does not pass G1.

## Build and startup

- The unattended Python commandlet rebuilt production assets, staged copied
  props and saved Lvl_KL_School3_G1. Exit 0 and G1_BUILD_AND_STAGE_COMPLETE.
- An offscreen editor initially waited for the autosave recovery modal before
  loading a map. Installed UnrealEd source identifies that modal and its
  unattended guard. Autosaves were preserved before restarting the identified
  agent-owned session. The unrelated editor was left alone.
- The replacement editor loaded the production map, advanced frames and
  answered MCP. Remote Python was enabled ephemerally on loopback.

## Repaired defects

1. Restart required bEnded but omitted Enter, automatically loading the old
   map at completion. It now requires both and uses the production map name.
2. The classroom occupied +Y while its doorway was on -Y. The copied hall
   opening, trim and jambs now connect to the classroom. No original map edit.
3. The camera ray multiplier was promoted to vector * vector. Its unconnected
   scalar value did not establish a scalar type. A connected double literal
   keeps the 260 cm ray aligned to the camera; the generator checks its type.
4. HUD fractional coordinates were promoted to integer multiplication, leaving
   labels at the origin. Connected double literals preserve fractional values.
5. The uncollected-book prompt selected the consumed text. Its two choices now
   match bConsumed, with runtime assertions for both states.
6. Copied school lights now read back the intended RGB channels. The inspected
   subsequent gameplay capture removes the preceding red/magenta cast.

## Runtime evidence

- G1_traversal_trial.json: real Move Blueprint and CharacterMovement collision
  from the entry through six waypoints into the classroom, followed by a
  camera trace focusing the production attendance-book component.
- G1_runtime_trial.json: Blueprint debug calls with real world timers; fresh
  initialization, prompt states, idempotent document collection, tape acquire,
  incomplete-playback rejection, mode-change cancellation, delayed completion,
  corroboration gating and the final prototype beat.
- G1_before_hud_light_repair.png is an actual game-viewport Shot, inspected:
  all labels overlap at top left and the scene is saturated red/magenta.
- The later gameplay Shot was also inspected: label positions are separate,
  and walls/desks have a normal color range. Readability and art remain below
  the quality bar. These are viewport captures, not a packaged-game result.

## Remaining requirements

No physical-keyboard proof, canonical whole-sentence reconstruction, four-tier
attention consequences, save/load, all chapters/endings, release verifier or
packaged Windows game is established here. Existing audio is a timing fixture;
it does not contain approved dramatic performances. Next implement the canonical
school loop and replace the cramped canvas journal with readable, wrapping UI.
