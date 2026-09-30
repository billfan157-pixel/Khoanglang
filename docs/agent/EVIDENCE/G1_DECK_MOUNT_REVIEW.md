# G1 cassette support: source and validation

Final checkpoint update (2026-10-01): G1_deck_mount.json records actual shelf
authoring/save and strict native vector readback. G1_navigation_trial.json
reached the deck through native movement and acquired it through a real camera
ray as part of the passed26-point route. Final front/side/back images exist;
front and side were inspected: shelf support and removal of cap spikes are
visible, while lighting response/source-art quality remain unaccepted. The
pre-execution notes below document the original investigation, not current
execution status. Cook/runtime evidence is in the checkpoint build/runtime
reports; normal shutdown is still an independent binary/environment failure.

`tools/g1_mount_deck.py` was prepared without editor execution. Python syntax
passed. A pure Python geometry evaluation produced 92 triangles, finite local
coordinates, bounds `(-45,-37,83)` to `(68,37,122)`, and no degenerate UV or
geometric triangles. This does not prove native rendered tangent quality,
collision or visual acceptance.

Run only after the school mesh repair succeeds and the corrected cassette
mesh is actually adopted in the saved G1 map:

```powershell
python tools/ue_live.py tools/g1_mount_deck.py
```

The script authors a distinct new mesh using copied G1 WoodDark/Metal
materials: a 4cm timber plank, two wall plates, two horizontal arms and two
diagonal steel supports. The plank's world bounds are X1885..1998, Y-37..37,
Z118..122; brackets meet X1998. Its top matches the corrected cassette's base
at Z122. The whole case and rear cable to about X1973 sit above that footprint.
It places an owned movable shelf actor with exact triangle collision and
rotates only the G1 cassette actor to yaw -90, so its original negative-Y
front faces into the negative-X hall. Interaction tag, entity reference,
materials, mesh and cassette collision are retained.

The source never builds an existing rendered shelf mesh. Existing owned
copies need valid bounds, native buffer checks and exact collision before
reuse; an invalid existing copy aborts for a distinct authored version. Only
a fresh mesh gets CPU access and the regular native build. Rendered positions,
normals and tangents must pass the helper's strict audit before saving.
Original geometry/material assets are neither overwritten nor deleted.

After the actual run, inspect `G1_deck_mount.json` and fresh front/side/back
PIE images at the current measured lighting. Confirm the cassette rests on
the plank, brackets meet the wall, and the one legitimate cable is visible
without cap spikes. Re-run the deck interaction ray and actual movement
approach: the shelf must not intercept the intended cassette prompt, hide its
controls or block the hall route. Include the whole canonical engineering
suite and fresh cook warning checks before claiming the scene is qualified.
Lighting and source art remain subject to user review; this is a functional
support and orientation repair, not a completed hero-asset claim.
