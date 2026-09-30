# Decisions

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
