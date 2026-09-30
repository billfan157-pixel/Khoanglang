# Release pipeline source and initial preflight — 2026-09-30

## Scope and observed results

`tools/verify_release.cmd` (or `.ps1`) forwards to the stdlib Python coordinator.
The default gate is **release**, and earlier PIE/engineering JSON cannot qualify
it. This is packaging infrastructure, not G1/G5 completion. HUMAN_SIGNOFF.md is
never created, read as a substitute for runtime proof, or edited by this tool.

Initial source checkpoint: a9e7f63a889467cd33e47a039f8e62dd0f4b3cca;
the working tree contains concurrent production edits. Each actual run records
its fresh revision/status, content/config hashes and candidate file manifest.

Verified read-only on this machine:
- UE installation reports 5.8.3, changelist 58210709.
- InstalledBuild.txt, RunUAT.bat, AutomationTool binaries, UnrealEditor-Cmd.exe,
  Win64 UnrealGame Development/Shipping and corresponding receipts exist.
- Installed WinPlatform.Automation.cs stages vc_redist.x64.exe and
  vc_redist.arm64.exe with -prereqs; both supplied files exist. The command
  bundles those prerequisites without installing anything on this computer.
- Installed AutomationTool ProjectParams.cs selects UnrealGame for a non-code
  project and parses skipbuild into client/editor build skips.
- Project descriptor is Blueprint-only. Installed prebuilt Development target
  is therefore the attempted route; no compiler or SDK installation is attempted.
- Windows Kits 10 contains UnionMetadata only; SDK Lib/Include and MSVC were
  not demonstrated. This is **not** an SDK suitability claim.
- Content measured 21,377,878 bytes during the initial inspection.
- Original DefaultEngine.ini was neither read nor printed; original assets,
  descriptor and configuration are not modified by packaging.
- `python -m py_compile tools/verify_release.py` succeeded.
- Default invocation returned exit 1, `qualified=false`, missing
  tools/release_runtime_plan.json. Campaign runtime support remains absent.
- G1 package-only preflight returned exit 1 because the canonical map was not
  saved yet; all installed-engine file prerequisites passed. The exact run's
  JSON is under ignored `_release_work/20260930_205146_6445b96a`.
- No UAT/cook or additional editor process was started during this preflight.
- An actual isolated-source exercise copied and hash-matched 454 content files,
  produced only the three intended config files, excluded all five editor
  plugins, and rejected an unbound earlier engineering report. Recovery source
  is `_release_work/isolation_test_5150760c`; source_manifest.json records hashes.

## One command and isolation

From project root:

```powershell
.\tools\verify_release.cmd
# Inspection only, while the campaign driver is absent:
.\tools\verify_release.cmd --gate g1 --package-only --preflight
# Once the canonical map is saved and asset writers are idle:
.\tools\verify_release.cmd --gate g1 --package-only
```

Each invocation writes `_release_work/<time_nonce>/result.json`. G1 package-only
returns **2 even after a successful package**, with
G1_PACKAGE_BUILT_RUNTIME_UNQUALIFIED, so it cannot be confused with a gate pass.
Preflight returns 0 only for prerequisite inspection and always qualified=false.
The packaged Development executable is a playtest candidate, not a Shipping RC.

The staging source copies Content rather than junctioning it. It copies only
DefaultGame.ini and DefaultInput.ini after checking for secret-bearing key names;
it generates a fresh DefaultEngine.ini with explicit map/culture settings.
MCP, EditorToolset, Python, Editor Scripting and modelling editor plugins are
excluded from the isolated descriptor. Original editor settings are not copied.
Unused GameplayStateTree and Landmass are explicitly disabled in the isolated
descriptor after a serialized-import scan. Future dependencies on those plugins
fail the scan and require a supported packaging route; they are not silently cut.
Source hashes bind this isolated candidate; original files remain untouched.

Actual UAT argv is saved as uat_command.json. The attempted command uses the
installed RunUAT with BuildCookRun, skip native compilation, explicit Win64
Development, cook/stage/pak/archive/package, and explicit canonical map(s).
Output goes to isolated uat.log and WindowsBuild. Missing binaries/pak files or
nonzero UAT exit fail. The maximum initial cook wait is 1,800 seconds; errors
retain the staging directory for diagnosis. Builds should be serialized with
editor asset saves to avoid capturing concurrent source changes.

## Runtime contract still requiring implementation

Neither release_runtime_plan.json nor a real packaged runtime driver is
invented by this change. To qualify, implement them against actual campaign
debug commands and production save state. A `kl.runtime-plan.v1` plan identifies:
gate, checked-in tools/*.py driver, cook maps, key screenshot locations, seven
chapters for release, and executable debug_commands for each case. Release
cases are A_public, A_private, B_public, B_private, C_public, C_private. G1 cases
cover dual listening, whole sentence preview/seal, four attention tiers,
teacher/child loop, Lâm corroboration and physical controls.

The coordinator invokes the driver once with `--request <runtime_request.json>`.
The request provides a unique nonce, source/candidate SHA, plan, package path,
and report path. The driver must actually launch the packaged game, exercise
every case and write `kl.packaged-runtime.v1` evidence in this run directory.
Required fields are enforced in validate_runtime():
- Exact candidate/source/nonce binding; packaged-win64 runtime; requested gate.
- Every case's executed debug commands, observed states and hashed trace;
  release also requires new-game start, ordered chapters 1–7, ending and truth.
- All seven chapter-boundary saves: restarted process, matching pre-save/loaded
  state hashes, actual hashed save file and execution trace.
- PNG captures for each key location at 1280x720 and 1920x1080; checks validate
  actual PNG dimensions and hashes. Screenshots still require visual inspection.
- Vietnamese rendering trace, rendered text, zero reported missing glyphs and
  successful runtime glyph/layout check. Text literal presence alone is not proof.
- At least 1,800 positive finite frame-time measurements, hardware identity and
  peak memory. Raw measured data computes p95 and enforces provisional 33.3 ms.
- Candidate files must remain unchanged throughout verification; runtime logs
  and saves belong in the run evidence directory, outside the package tree.

This contract coordinates evidence; it cannot make a nonexistent campaign
playable. Audio loudness/spectrum and user listening/scare review remain separate
required work; a runtime driver cannot certify human acceptance.

## Provenance and unresolved blockers

Existing engine and First Person template provenance: the user's Epic Games
UE 5.8.3 installation. This document records origin only; it does not certify
the user's Epic license, a complete third-party asset inventory or distribution
rights. No asset is downloaded or purchased by this pipeline. Those reviews
remain outstanding before an RC claim.

Next executable step: wait for saved canonical school map, then attempt isolated
G1 package-only cook. Native-target/plugin compatibility, SDK independence,
standalone rendering and successful executable launch remain unproven until
that actual attempt. No campaign, endings, boundary saves, packaged runtime
driver or release candidate is presently demonstrated.

## Actual saved-school cook attempt

After the main agent confirmed the canonical map saved, the pipeline froze the
copied assets and attempted actual UAT. G1_WINDOWS_COOK_TRIAL.json records the
exact source/asset/log hashes, failure categories and recoverable directories.

The Windows cmd wrapper had a nested-quoting defect, repaired by constructing
the native cmd /s /c string once. UAT then reached a genuine sandbox restriction
on its AppData logs; authorized escalated execution allowed those engine logs.
GameplayStateTree enabled in the original descriptor made this nominally
Blueprint project require new native targets. A static scan of all asset files
found no StateTree imports; the isolated descriptor now explicitly disables it.
The original descriptor remains unchanged.

Actual cook run: `_release_work/20260930_211515_19983cdc`.
Observed source revision a9e7f63a889467cd33e47a039f8e62dd0f4b3cca;
snapshot SHA256 424f8325884de83d7303a47eae70ffe94182597dc2e27fbc0aa7d96de97e8ae6.
UAT exited 25; cook exited 1 with 23 errors and 20 warnings. It reached real
Windows asset cooking/global shaders, with 2,136 MB peak physical memory.
AutoSDK validation explicitly marks native Win64 SDK invalid; installed-target
content cooking nevertheless ran. No Windows package was produced.

Fatal asset issues: BP_KL_SchoolCharacter contains null EnhancedInputAction
events/orphan action-value pins; original FirstPersonCharacter also has null
actions; ABP_FP_Copy has no skeleton. Landmass default startup materials depend
on NeverCook editor resources. The pipeline now disables unused Landmass after
the same import guard; fresh prerequisite-only inspection succeeds and remains
unqualified. That fix has not yet been confirmed by a new cook.

Material/mesh warnings are also real blockers to visual acceptance:
M_KL_ART_Surface has an invalid normal sampler/default texture and missing
Saturate input (fallback material); Notice_Board, Wall_700 and Door_Frame report
NaN bounds. Original assets require review/repair by their owning agent. This
packaging task did not modify them or mask compiler errors.

Next executable step: repair/save the canonical character dependencies, then
rerun the same G1 package-only command from a fresh isolated snapshot. Runtime
qualification and the complete campaign remain outstanding regardless of cook.

## Windows Development package produced after asset repair

G1_WINDOWS_PACKAGE.json records the exact successful candidate. The owning
agent saved an independent native Character/GameMode and replaced the broken
core graph. All earlier EnhancedInput and animation skeleton errors disappeared
in the next cook, without excluding FirstPerson assets. That retry retained
eight Landmass startup-package errors despite Enabled=false in the descriptor.

Installed source UProjectPackagingSettings.h:178 declares config=Game. The
coordinator now generates packaging settings in isolated DefaultGame.ini, while
GameMapsSettings remain in DefaultEngine.ini. Installed cook source converts
DirectoriesToNeverCook mount paths to local paths. The isolated recipe excludes
the unused /Landmass startup mount only after the import guard found zero game
references; future serialized Landmass references fail before cooking.

Actual success: `_release_work/20260930_214738_28dac5b5`, UAT exit 0, BUILD
SUCCESSFUL; cook/stage/package/archive completed. Artifact contains 50 files,
909,806,066 bytes, with bootstrap executable, UnrealGame Development binary,
pak/IoStore containers and supplied VC x64/arm64 redistributables. No files for
MCP, EditorToolset or PythonScriptPlugin are in the archive manifest.

Frozen source SHA256:
ebb19702a06853f08c64c1653b868f44d3d2a4b896007f081e0c74f62a717333.
Whole artifact SHA256:
8943b0d4065fe8600b151c7e1a867a542d4523c297d7c6d32d56b286ae32effb.
Executable is `WindowsBuild/KhoangLang0217.exe` directly beneath the run folder;
retain the entire WindowsBuild directory with it. Source/asset/artifact manifests
and full uat.log remain in this recoverable run directory.

This is **G1_PACKAGE_BUILT_RUNTIME_UNQUALIFIED**, not G1 acceptance, a Shipping
candidate or a complete campaign. Cook warnings about old material fallback and
NaN mesh bounds remain recorded in the package evidence. No packaged executable
has been launched by this packaging task. Next step is standalone game launch,
actual control/loop checks, screenshots and performance measurement against this
exact source/artifact, followed by the remaining campaign and release work.
