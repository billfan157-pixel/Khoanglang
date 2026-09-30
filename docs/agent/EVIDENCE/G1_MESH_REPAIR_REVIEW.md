# Bounded G1 mesh investigation and repair source

Final checkpoint update (2026-10-01): the historical investigation below is
superseded for execution status by G1_school_mesh_repair.json and
G1_mesh_binding_audit.json. All four explicit repairs and all51 adopted map
meshes passed actual native buffer/bounds audits after reload. Source provenance
is recorded for50 meshes; the new shelf has project-authored provenance.
Nonzero triangle counts match originals after removing only64 zero-area window
faces and10 zero-area faces each in pupil desk/bench. Final cook has no reported
NaN/ShaderMap/degenerate errors. Actual packaged capture still exits777003;
empty Engine Entry reproduces this independent shutdown failure. Visual quality
remains unaccepted. See G1_CHECKPOINT_RUNTIME.json for scope and controls.

Baseline checkpoint observed: `df7ae853cadab9806969a48bc9186f30770ab888`.
No shared-editor execution, source-asset edits or new cook occurred while
preparing `tools/g1_repair_school_meshes.py`. Python syntax passed.

The owner's first actual execution saved the notice-board copy with finite
bounds and valid read-back normals/tangents, then failed the wall's strict
tangent audit. No actors were remapped. A later safe retry reused that board
without rebuilding it; the wall still had six exact zero rendered tangents
after both Mikk and non-Mikk recomputation. Actual native source audits found
120 triangles and no degenerate UVs or geometry. Failed vectors occur at the
endcap/weld boundaries, including X +/-350, Y 0, Z 110 with normals +/-X.
Smooth welded topology causing tangent cancellation is a repair hypothesis,
not an exclusive root-cause finding.

The current bounded correction copies every native wall triangle corner into
a fresh description with independent vertices. It preserves exact coordinates,
winding, UV0 and three native material groups; only smoothing connectivity
changes. Installed `StaticMeshOperations.cpp` recomputes normal groups per
connected VertexID. The source description itself is read-only. A probe
confirmed three dense groups, LOD material indices 0/1/2 and one UV channel;
other layouts abort instead of silently losing attributes. No geometry is
simplified. SHA256 fingerprints of all ordered triangle corners/groups must
match before and after the native regular build. The same strict rendered
normal/tangent audit and matching rendered triangle count gate saving.

Offline execution of the actual isolation helper against the original wall
authoring function produced 78 welded source vertices, 360 independent copy
vertices and the same 120 triangles with identical ordered corner/UV/group
fingerprints. Every analytic per-face tangent was nonzero and orthogonal to
its face normal (maximum dot 0); UV and geometry degeneracy counts were 0.
This checks source logic and math only. Python syntax passed; the revised
Unreal build, native TBN readback and cook are still required.

The retry crashed inside `BuildFromStaticMeshDescriptions` on the already
built notice-board copy (`FRenderResource deleted without being released
first`). Its saved copy and originals remain preserved. The script now never
calls that API on a built mesh. Existing owned copies are reused only after
read-only position, bounds, material/collision and strict buffer checks;
invalid copies remain intact and a distinct version is created. Buffer
inspection no longer toggles CPU-access on existing assets. Only newly
created meshes get that flag before their first build. The native LOD setter
uses `PostEditChange`, whose installed static-mesh code recreates render state
and waits its release fence. The safe reuse guard completed in the owner's
third run without a crash, but that run failed the wall's tangent audit. This
does not qualify the latest isolation correction or a complete repair.
Known corresponding G1 material-copy bindings are permitted during read-only
reuse, while different slot names or unexpected interfaces still abort.

## Actual evidence and source findings

The real UAT log in `_release_work/20260930_214738_28dac5b5/uat.log`, lines
240-254 and 643-645, reports NaN serialized bounds for production copies of
`SM_KL_Wall_700`, `SM_KL_Notice_Board` and `SM_KL_Door_Frame`, with NaN card
representation data on two of them. The package eventually built; warnings
must not be recast as a failed cook or silently suppressed.

`kl_mesh.py` fills positions and UVs but not normals or tangents, then uses
`build_from_static_mesh_descriptions` with its default fast build. Installed
UE source `StaticMesh.cpp` shows that the fast vertex-buffer path copies
normals/tangents verbatim. Its fast cache-building branch does not perform the
same render-data bounds assignment as the regular `StaticMeshBuilder.cpp`
path. This makes an explicit regular rebuild a focused repair candidate.
It is not a proven exclusive cause until finite source data and a clean cook
have been verified. Existing editor bounds are not proof of cooked bounds.

The actual `G1_refined_deck.png` contains multiple triangular shapes below
the deck. Source inspection found a separate geometry defect: three Y-axis
cylinders in `prop_tapedeck` use Z-centre `z0` for their body, while
`MeshBuilder.cylinder` uses `cy` for cap-centre Z. A pure Python execution of
the original authoring function and corrected builder, without Unreal, gave:

| Version | Triangles | Minimum XYZ cm | Maximum XYZ cm | Finite positions |
| --- | ---: | --- | --- | --- |
| Original function/helper | 428 | -23, -18.6, -18.2 | 23, 43.2024, 29 | Yes |
| Corrected cap centres | 428 | -23, -18.6, 0 | 23, 43.2024, 29 | Yes |

Thus those caps demonstrably extend below the authored casing; this is
malformed geometry, independent of shader normals. The one rear cable from
`(0,17,8)` to `(0,43,2)` is intentional and retained. The image also clips
severely, so it cannot establish material/tangent quality or the final shape.
The source correction keeps triangle count, body vertices, original winding
and UVs, while changing only cap-centre Z for those cylinders.

## Executable scope

With PIE stopped and `G1Canon/Lvl_KL_SchoolSlice` loaded, the editor owner runs:

```powershell
python tools/ue_live.py tools/g1_repair_school_meshes.py
```

The script copies the three production school meshes and the existing G1
deck to fresh distinct `_Regular` mesh assets in G1Canon. The actual native
probe confirmed `VertexID(id_value=0)`, description position reads and LOD
build settings. It also confirmed `bDoFastBuild` is protected; the script does
not bypass that boundary. A fresh StaticMesh constructor initializes the flag
false, while duplicating an existing mesh would retain its fast-build flag.
It rejects non-finite source positions instead of replacing unknown
coordinates, asks the native regular builder to recompute normals/tangents
and bounds, preserves material slot names and body collision flags, and remaps
only actors in this G1 map while preserving component material overrides.
The native LOD build-setting setter calls `PostEditChange` and `Build` in the
installed engine source. The deck is regenerated from only its original
authoring function using a corrected local builder; importing the whole
asset-writing original script is deliberately avoided.

Actual finite bounds are required before saving a copy. If the engine already
exposes its native ProceduralMeshLibrary buffer reader, positions, normals and
tangents are checked; otherwise the report explicitly marks buffer readback
unqualified. The script enables/installs no plugin. Source package hashes are
checked before/after saving each copy. Failure writes a `FAILED` report and
does not claim repair. The owner still needs to execute the complete script.
Non-complex source collision requires a separate aggregate-collision copy;
this script aborts rather than discard those hulls. Existing repair-owned
targets are checked by source-origin metadata before reusing them.

## Qualification still required

1. Inspect `G1_school_mesh_repair.json` for finite position/bounds audits,
   fresh regular-build provenance, matching slots/collision and source package
   hashes. A successful script save is editor engineering evidence only.
2. Inspect fresh deck images from the front, side and back at readable
   exposure, with flashlight off/on. Confirm artificial cap spikes disappear
   and the retained cable is one continuous cylinder. Check wall and frame
   silhouettes for smoothing changes caused by recomputed normals.
3. Run real pawn movement through the corridor and classroom doorway and the
   full interaction engineering case. Exact collision must preserve the open
   doorway, threshold, notebook side approach and furniture boundaries.
4. Produce a fresh isolated package/cook. Search its complete log for NaN
   bounds/card data, bad tangents and static-mesh build errors. Verify map
   dependencies reference the new copies. If original warnings persist, trace
   their remaining dependencies instead of filtering or hiding them.
5. Run the packaged map and inspect culling, shadows, clue visibility and
   frame timing. No clean-cook, visual or runtime acceptance claim is justified
   until these checks pass. Main owns the separate exposure/flashlight work;
   this script does not change lights, player code, materials or canon.
