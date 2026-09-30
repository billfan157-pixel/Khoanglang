# G1 isolated art refinement: execution and acceptance requirements

Status: source prepared; no editor execution, screenshot comparison, shader
compile, cook or performance claim was made by the author of this script.
The inspected input was `G1_canonical_entry.png`, an actual PIE image with the
new canonical Vietnamese HUD. Its ceiling clips, near-wall flashlight pool
dominates, and floor/doorway detail is lost in darkness.

The shared-editor owner's first execution stopped while wiring the Abs
expression, before material compilation or map saving. Native probing showed
that unary pins report `None`, while their C++ property is named `Input`.
The source now resolves all destination pins from the engine's native input
name list, converting the unnamed unary pin to an empty name as required by
`MaterialEditingLibrary.cpp`. This repair passed Python syntax only; a new
engine run is still required. The copied master graph is rebuilt on rerun.

The second integration run compiled and saved the copied master, then stopped
on a false return from the scalar setter while preparing the floor instance.
Installed `MaterialEditingLibrary.cpp` shows that this UE implementation writes
the value and updates the instance, but returns an untouched false flag. The
source now validates parameter existence and engine readback with tolerance,
and uses the native material-parent setter plus a parent readback. A subsequent
full engine run and capture inspection remain required before acceptance.

`tools/g1_refine_school_art.py` writes only copied material assets below
`/Game/KhoangLang/Production/G1Canon/Materials` and material/light/postprocess
overrides in `G1Canon/Lvl_KL_SchoolSlice`. Mesh assets, source textures and
source worlds are unchanged. It requires PIE stopped and the isolated map
loaded. Run only through the shared-editor owner:

```powershell
python tools/ue_live.py tools/g1_refine_school_art.py
```

The source reuses project-authored `art_tex.py` plaster, roughness and grunge
maps. It gives plaster a 160 cm world-projected scale, restrained lower-wall
damp staining, neutral rough surfaces and flat plaster normals. UV-mapped
furniture keeps its source texture family, with normals blended from a flat
normal and normalized. This removes the source graph's ineffective operation
of multiplying every normal channel by the same strength. No external art
source or rights are implied.

Local light intensity units are explicit lumens with bounded radii. Shadows
stop practical and window lights from illuminating through solid walls; this
has a performance cost that must be measured. Lamp emissions are capped while
already dead lamps stay below that cap. Moonlight is restrained cool white,
practicals are local warm white, and postprocess has neutral colour grading,
fixed manual exposure, lower vignette/AO and no motion blur. The numeric
values are an initial reversible tuning pass, not final photometric claims.

The following integration evidence is required before accepting the result:

1. Confirm no BS_ERROR or native shader compile error; require the script's
   `G1_canonical_art_refine.json` and a saved isolated map. Inspect material
   references to confirm no actor override points at DefaultMaterial and no
   source material or mesh package was saved by the script.
2. Capture fresh PIE images with timestamp-resolved screenshot filenames at
   entrance `(-880,0,98)` facing `+X`, hall `(300,0,98)` facing `+X`, classroom
   doorway `(870,180,98)` facing `+Y`, and book approach `(1040,650,98)` facing
   the notebook `(1050,790,100)`. Verify camera view location on the capture
   frame; actor teleport alone may not settle the view. Repeat flashlight off
   and on using the actual F binding, and repeat at 1280x720 and 1920x1080.
3. Inspect images: ceiling paint remains visible outside the luminous tube;
   door edges and floor boundaries remain navigable with flashlight off;
   book cover, desks and lower-wall water traces remain legible. Check
   plaster grain does not become oversized gravel, texture seams do not
   switch projection visibly on bevels, and no cyan/orange full-room wash
   replaces local contrast. Histogram clipping percentages can diagnose
   capture problems; they cannot establish visual quality.
4. Run actual pawn movement and ray-interaction checks after the art pass.
   No walkable space or clue visibility may be obstructed. Do not mislabel
   placeholder child meshes as completed Lâm or Vân character art.
5. Measure a packaged standalone 1280x720 low run on the discovered integrated
   Intel Arc hardware: 1800 measured frame times, median/p95, peak memory,
   and shadow GPU cost. The provisional target remains p95 <=33.3 ms. If
   shadows fail, reduce selected shadow lights only after testing remaining
   wall occlusion; do not claim qualification from editor frame rate.
6. Add the exact resulting build/hash, room captures and questions to the
   user review queue: does this read as a worn Vietnamese primary school,
   is evidence readable without developer knowledge, and does the balance
   of warm fittings/cool night support the investigation? Human judgment,
   character art and audio/scare acceptance remain outstanding.

Integration should also inspect the copied player's flashlight component.
Its hard near-wall hotspot is visible in the input capture; this script does
not change that Blueprint because another agent owns the player generator.
Any later lamp tuning must be made in the generator/copied player only, never
in the retained source player. Preserve an image comparison and input trace.
