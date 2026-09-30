# G1 foundation checkpoint — not a gate pass

All new assets are under `/Game/KhoangLang/Production`. The original maps,
components and character remain preserved. Build scripts retain the prototype
story beats as engineering fixtures, not completed canonical campaign content.

## Changes

- Return construction no longer replaces the function-entry execution body.
- Branch continuation uses Sequence; Boolean operations use typed native nodes.
- Audio controls use explicit Engine.AudioComponent functions, avoiding palette
  name collisions with SynthComponent.
- Character copied from baseline; old gameplay components replaced with
  production classes. Move/Aim/Jump handlers restored. View-directed line trace
  and validity guards replace a zero-length sphere search.
- HUD positions and rectangles multiply fractional layout by actual viewport
  dimensions. This is a layout repair, not typography/accessibility acceptance.
- Latent function delays replaced by component-owned world timers. Latest
  source schedules reply after measured 13s roll call and completion after 3.2s.
- Filter choice cached before mutating state, avoiding recomputation of the
  inverse on later subtitle/tape calls. Corner visual changes exclude ordinary
  evidence props.

## Evidence limits

G1_core_build.json and G1_player_build.json show successful final compilation.
The template-level staging path subsequently saved the production map. The
offscreen startup stall was traced to an autosave recovery modal and resolved
with preserved recovery data and an unattended agent-owned editor.

G1_RUNTIME_REPAIR.md records the later defects and fixes found by actual PIE.
The runtime trial now passes collection/prompt states, interruption/full
completion of the 16s tape and prototype beat timers. A separate route trial
passes real CharacterMovement collision and camera focus in the classroom.
Neither trial proves physical keyboard input, canonical endings, save/load,
scare quality or the complete G1 loop. Source audio reports remain source-only.

Next: implement canonical sentence reconstruction and consequential attention,
with readable wrapping UI, then qualify the school against the G1 quality bar.
