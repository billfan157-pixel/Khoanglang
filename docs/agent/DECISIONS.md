# Decisions

## 2026-09-30: Recover the unattended editor without restoring original assets

Engine source shows that a pending autosave recovery dialog is offered before
map load unless FApp::IsUnattended is set. The offscreen editor stalled before
frame 1. Preserve all Saved/Autosaves data in the ignored recovery backup;
stop only the identified agent-owned session and restart with -unattended.
The production school then loaded and MCP responded. Do not clear the user's
autosaves or stop the unrelated editor process. Reversible via the backup.

## 2026-09-30: Correct promoted math pins using connected scalar literals

Runtime evidence showed a reachable book could not be focused, despite a
matching Python ray hitting it. The generated vector multiplier had become
vector * vector. A connected MakeLiteralDouble keeps its distance scalar.
The HUD multiplier likewise needs a connected double fraction before SizeX/Y;
otherwise Unreal promotes the operation to integers and the fraction becomes
zero. Assert these pin types during generation. Production copies only.

## 2026-09-30: Keep restart explicit and preserve production map routing

The prototype restarted as soon as bEnded became true. Require Enter as well,
and route the production character back to Lvl_KL_School3_G1. Debug playback
verification now retains the same world through completion. This remains a
prototype scene ending, not a campaign ending.

## 2026-09-30: Repair runtime on production copies

G0 exposes bypassed function bodies, disconnected input handlers, HUD coordinate
mismatch and art-map spawn failure. Use a production namespace and copied map.
Alternative: overwrite baseline assets. Copies and ffc85df LFS snapshot preserve
comparison and rollback. Do not claim the original slice works.

## 2026-09-30: Adopt the user's revised V3 story

Copy the new Downloads file byte-for-byte to the canonical story path. Preserve
the prior complete 29/09 V3 as a separate file. The revised source resolves
the earlier T2 access, partial network, and ending construction questions and
is the reference for future narrative work. No story text was rewritten here.

## 2026-09-30: Establish G0 before more content
The new production brief requires gate evidence. Preserve the current prototype
and qualify its actual behavior before expanding the campaign. Alternative:
continue expansion on unverified graphs. Reversible: yes, no assets removed.

## 2026-09-30: Narrow asset saves
Save one requested asset, not its entire parent folder. The prior helper saved
unrelated siblings and logged success even when Unreal returned failure.
Keep explicit directory saves supported. Reversible via Git.

## 2026-09-30: Protect existing local configuration
Exclude DefaultEngine.ini from the initial commit because it contains a local
token. A sanitized distributable configuration remains required. Do not expose
the token in evidence or change it without a concrete need.
