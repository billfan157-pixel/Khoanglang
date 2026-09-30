# Decisions

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
