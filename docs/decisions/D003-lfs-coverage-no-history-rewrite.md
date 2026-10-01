# D003 — LFS coverage: add patterns, fix the check, no history rewrite

Date: 2026-10-01. Decided by the agent during Task 2.0 skill setup.
Supersedes the first version of this record, which repeated the preflight's
"492 plain blobs" figure without verifying it. That figure was wrong; see
"What the census found".

## Context

`git_preflight.py` reported three problems after the seven skills were installed:

1. `.gitattributes` did not send seven required extensions to Git LFS:
   `.ogg .mp3 .flac .exr .hdr .psd`. The project is audio-driven
   (environmental audio plus the T1/T2/T3 tapes), so audio formats matter most.
2. 492 binary files "match an LFS pattern but are stored as plain blobs".
3. One file over 5 MB without being an LFS pointer:
   `docs/agent/EVIDENCE/G1_merged_editor_runtime.log`, 55.3 MB.

## What the census found

Before doing anything irreversible, the claim in (2) was measured directly.
[SCRIPTED], using `git rev-list --objects --all` plus `git cat-file`:

| Measurement | Result |
| --- | --- |
| Unique LFS-pattern objects in history | 536 |
| Of those, stored as LFS pointers | 536 |
| Of those, stored as plain blobs | **0** |
| Tracked LFS-pattern files in HEAD | 492 |
| Tracked files git stores as real content | **0** |

So (2) was a **bug in `git_preflight.py`, not real debt**. The script read files
from the working tree. After `git lfs checkout`, LFS has smudged every pointer
back into real content on disk, so no file in the worktree looks like a pointer
any more. The script reported all 492 as plain blobs.

Fixed in `33f1551`: the check now asks git what it stores
(`git cat-file -p HEAD:<path>`) instead of reading the worktree. This mattered
because the false reading would have justified a pointless history rewrite of a
multi-hundred-megabyte repository.

Consequence: `git lfs migrate import` is **not needed**, and running it would have
been pure damage.

## Decision

1. **Add the seven missing patterns to `.gitattributes`** (`b104588`). Forward-only,
   no history change. `git_preflight.py` reports "LFS coverage: all required
   extensions are covered" [SCRIPTED].
2. **Do not run `git lfs migrate import`.** Not because it is forbidden in
   principle, but because there is nothing to migrate [SCRIPTED]. Independently,
   it would rewrite all 32 commits, change every hash, invalidate the review
   checkout `KhoangLang0217-g1-review-8220edf` and the checkpoint references in
   `docs/agent/STATE.md` (`8220edf`, `439582a2...`), and consume GitHub LFS quota,
   which `kl-repo-hygiene` warns is limited.
3. **Untrack the 55 MB log** (`70bae4b`), keeping the file on the developer's disk.
   `.gitignore` already carried `docs/agent/EVIDENCE/G1_*.log`; the file had been
   force-added past it. The evidence `docs/decisions/D002` cites from that log is
   preserved verbatim, with Windows error codes and source line numbers, in
   `docs/agent/EVIDENCE/G1_merged_save_failures_excerpt.md`. `D002` was updated to
   point at the excerpt. Machine-specific paths are stripped from the excerpt
   (verified: zero occurrences of a home directory or `../` walk) [SCRIPTED].

## Remaining debt, accepted

- The 55 MB blob is still **reachable in history** at
  `6e97a66e353f92be6d4095d0715521c68819182d`, added in `1eaede4` [SCRIPTED].
  Untracking stops future growth but does not shrink history. Anyone cloning the
  repository still downloads it. Removing it means either rewriting history or a
  fresh initial commit, both of which are the project owner's decision.
- No plain binary blobs in history [SCRIPTED]. Repository size is otherwise
  4.2 MiB of loose objects.

## Revisit when

- The developer decides the 55 MB blob in history is worth a fresh initial commit, or
- the repository moves to a private host and history rewrite becomes affordable, or
- a new asset type appears that `.gitattributes` does not yet cover, in which case
  add the pattern **before** the first file of that type is committed, because a
  binary committed as a plain blob stays in history forever.