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

G1_core_build.json and G1_player_build.json show successful final compilation
of their build runs. Later generator refinements listed above are pending
rebuild and runtime verification. Compilation is not a playable G1 proof.

Four production prop assets were saved before map staging failed. Calling
EditorAssetLibrary.duplicate_asset on a World then LoadLevel kept a standalone
world reference; engine reported old level package not cleaned up and fatal
World Memory Leaks. Original editor exited. No production map was saved.
The script now uses LevelEditorSubsystem.new_level_from_template, confirmed in
the installed engine source; the replacement path is pending execution.

Replacement editor PID 16464 is live, with increasing CPU and startup log at
frame 0. MCP observations timed out; that does not prove process termination.
No duplicate editor was started after those observation timeouts.

g1_runtime_trial.py is prepared but not run. It checks collection idempotence,
journal gating, interruption/full completion of the 16s tape, and prototype
beat timers in real PIE. It does not inject keyboard input, prove scare quality,
exercise canonical endings or prove save/load. Source audio report and spectrum
CSV measure 12 original placeholder WAVs, not the in-game mix or LUFS.

Next: let the confirmed editor finish startup, rebuild production copies, stage
the copied map through the template API, and execute/inspect the PIE trial.
