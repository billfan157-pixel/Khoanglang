---
name: kl-vietnam-world-research
description: Research real Vietnamese regional geography, historical 2002–2026 environments, rural architecture, schools, communal loudspeakers, dam infrastructure, objects, language and daily life to ground Khoảng Lặng 02:17's fictional Khe Lạc in evidence. Use for location/level art direction, environment storytelling, scene references, props, signage, dialogue-world detail, regional consistency, and Blender/Unreal scene briefs; not for unrelated coding fixes.
---

# Khoảng Lặng 02:17 — Vietnam World Research

Give Astra high-quality *situated evidence*, not a prescribed visual style. Turn credible Vietnamese source material into playable, culturally and historically coherent spaces while leaving art direction and engineering choices open.

## Activate only when the task needs real-world grounding

Examples: selecting Khe Lạc's geographic reference, designing the school/market/homes/communal broadcasting station/hydropower site, choosing 2002/2026 props, writing signs and ordinary dialogue, adding flood or weather traces, checking anachronisms, validating environmental storytelling. Do **not** demand a research dossier for a small material tweak, isolated input bug, or unrelated build operation.

Read `references/PROJECT_ANCHORS.md` when working with the fictional town, its chronology, or current G1 assets. Read `docs/research/KHE_LAC_REGIONAL_REFERENCE.md` for the proposed Đà Bắc / hồ Hòa Bình regional reference and its source ledger; it is a PROPOSED anchor awaiting the owner's decision, not canon. Read `references/SOURCE_ATLAS.md` for source discovery and `references/SCENE_BRIEF.md` when handing an environment or object to production. Read `references/SCHOOL_CASE_STUDY.md` only for School No. 3 or as an example. These references are research *starting points*, not authority above the current working tree or V3.

## Understand the specific fictional place

1. Inspect the current canonical `docs/story/Khoang_Lang_02_17_Cot_truyen_v3.md`, relevant sections first, and relevant `docs/agent/` production state. Verify which map or level is active before referring to art as current.
2. Khe Lạc is **fictional**. V3 describes a remote valley around a large reservoir with a hydropower installation; it does **not**, by itself, identify a real province, dialect, culture, or architectural region. Never invent that decision as settled fact. If a regional anchor is not approved, compare 2–3 plausible candidate regions and mark one as *proposed*, with physical/cultural implications and trade-offs. Continue reversible research and blockout without silently locking geography.
3. Build an evidence-backed **place logic**: topography → water/drainage → settlement and roads → public institutions and loudspeaker routes → materials/repairs → human use → what clues the player notices. Fit references to the *chosen* region, not to a generic collection of “Vietnamese” symbols.
4. Track **1998 / 2002 / 2003–2025 / 2026** separately when relevant. A building existing in 2002 may have been repaired, rewired, replastered, repurposed, or left intentionally unchanged by 2026. Record why; do not simulate age by uniformly adding dirt and decay.

## Research in the language and level of the question

- Search Vietnamese first for Vietnamese conditions, then academic/archival/English sources for corroboration. Search **specific place + period + object/use** (e.g. `trường tiểu học [candidate province] 2001 phòng học`, not just `vietnam spooky school`).
- Prefer contemporary archives, original dated photographs/plans, national/provincial statistics, government institutional records, museum collections, credible scholarship, and situated reporting. Community oral history and local photos can be valuable but need provenance. Style references, rendered game art, and generative images are **inspiration**, not evidence about actual Vietnam.
- For important claims capture the **exact proposition, URL or archive ID, issuing body/photographer, actual event year, publication year, geographic applicability, source type, confidence, license, and access date**. A contemporary rule must not be projected backward: for example a school program announced in November 2002 cannot establish what existed in Khe Lạc before the fictional September 2002 flood.
- Compare credible sources when design depends on contested facts. Distinguish observed fact from interpretation, national statistics from a specific locality, published policy from actual on-site implementation, and a regional analogy from direct evidence.
- Verify images in context: image search results may misdate, mislocate or miscaption photographs. Check the original host, caption, metadata when available, actual location/date, cropping, and rights. Link rather than importing photographs or copying artworks without authorization. A citation is **not** a reuse license.
- Treat real communities as people, not aesthetic props. Do not exoticize dialects, religions, minority customs, poverty or flood victims; do not fabricate customs or use identifiable testimony/portraits without appropriate permission.

## Protect the narrative without constraining creativity

Classify every consequential finding:

- **CANON:** stated in the designated V3; fictional truth, not an external historical claim.
- **VERIFIED REFERENCE:** supported by a specific external source within its actual period and locality.
- **ANALOGY:** authentic elsewhere, plausibly adaptable but not evidence for Khe Lạc.
- **DESIGN PROPOSAL:** invented connective tissue, architecturally/gameplay useful, not historical fact.
- **UNKNOWN / CONFLICT:** unsupported or incompatible claims needing more evidence or owner choice.

Keep source-derived fact, canon, and creative interpretation separate in notes, scene briefs and agent reports. Do not override V3's witness timeline, victim accounting, player knowledge, supernatural laws or revelation order with an interesting real-world analogy. Conversely, do not describe V3's supernatural acoustic behavior as authentic physics. An engineering plausibility check may **challenge a provisional story dimension**, but requires a documented design resolution; never silently rewrite canon.

Ask for the project owner's decision only when an unresolved choice would *materially lock* region, identity, canonical history, irreversible large-scale architecture, or costly rights/asset work. Make sensible reversible local choices autonomously.

## Convert research into something a game artist can build

Choose the smallest useful output for the task:

- **Quick reference answer:** 2–5 sourced observations and the affected scene/prop decision.
- **Regional identity brief:** plausible locations, terrain/rainfall/materials/architecture, typical public spaces, dialect considerations, consistency risks, and a recommended *hypothesis* awaiting owner decision if consequential.
- **Scene research brief:** use `references/SCENE_BRIEF.md`; identify historical layers, local routines, player route, clue sightlines, affordances, asset family, soundscape, signage, weathering mechanisms, lighting constraints, and source ledger.
- **Prop production note:** function, plausible date, reference, silhouette/construction, approximate measurements **tagged measured or provisional**, materials, transformations over time, camera/readability needs, Blender source/Unreal target, collision/interaction requirements, licensing.

A convincing space needs mundane use and causal history: who repaired the roof, why one room retains old benches, which notice was replaced, why a broadcast wire still crosses the lane, where flood marks could persist after repairs. Show *ordinary life first*; let horror exploit a meaningful deviation. Avoid decorative cultural collage and generic abandoned-asylum imagery.

When research informs Unreal/Blender work, translate from sources to **testable visual and gameplay hypotheses**, not fake certification. Verify real units, elevations, object clearances, sightlines, materials and collision in the production map. Cite only what the sources support; image quality, mechanical correctness and horror impact require actual rendered/gameplay review.

## Completion standard for a research task

Provide: (1) scene/design question answered; (2) specific, dated regional references; (3) what is canon vs evidence vs proposal; (4) implementable consequences; (5) unresolved claims and necessary approvals; (6) provenance/reuse rights for selected material. Label important facts by confidence. Do not claim to have visited locations, inspected restricted archives or watched/played media not actually accessed. No gratuitous dossiers or automatic production edits when the user asked only for research.

## Project-bound constraints worth remembering

- V3 contains *provisional engineering numbers* for the 2002 tunnel/flood; verify geometry and timeline before committing a detailed hydropower reconstruction. Seek expert review if physical credibility is central to a pivotal reveal. Never turn fictional hydropower plans into real-world operational advice.
- Earlier G1 reports describe coarse art, contrast problems and synthetic source audio. They are historical observations; inspect current images/asset state before repeating them. Do not equate asset import, compiler success or a dated JSON report with accepted appearance.
- Keep sensitive local configuration and tokens out of research artifacts. Avoid unnecessary personally identifying information, licensed-media downloads, paid services, or repository changes beyond the requested scope.
