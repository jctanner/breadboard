# Fullsend CI omits the completed strategy and review documents from artifacts

## Evidence

Real agentic-ci job 17329828389 in pipeline 2969118303 passed on 2026-10-20.
Host validation checked a completed dry-run result for RHAIRFE-3739 and the
post-script copied eleven verified business artifacts into
`.fullsend-state/17329828389/publish/handoff`. It assembled local reports with
publication disabled.

The GitLab artifact definition uploads only `fullsend-output/`. The ZIP has
40 files, including agent-result.json, fifteen session/agent transcripts plus
the journal, debug/gateway/security logs and cleanup receipts. It contains
zero standalone strategy/review files. The result lists their paths, but
neither their contents nor the private handoff/report directory is exported.

The pinned source's `run-fullsend.sh` sets `STRAT_PUBLISH_DIR` under the private
state directory and its exit trap copies only the host run/ownership/recovery
records into `fullsend-output/`. Native Fullsend retains outputs/transcripts;
its temporary downloaded repository is removed after the run. This explains
the missing business files without implying failed strategy generation.

## Impact

The functional dry-run is verified, but the artifact archive cannot reproduce
the final business snapshot or support direct file-based content judging.
Read the assessments/refinement edit from the retained transcripts; do not
represent those excerpts as byte-verified final files. The reviewed run's
excerpts and verification receipt are under its `review/` archive directory.

## Required fix

Export the allowlisted handoff, progress/completion records and assembled
reports into the public CI artifact directory before secret scrubbing/upload.
Keep credentials, gateway state, git metadata and arbitrary private workspace
files outside that export. Preserve original failure status and cover both
successful and partial/failed runs with model-free checks.

Do not broaden GitLab artifacts to all of `.fullsend-state/`: it contains
credentials and other private runtime state.

[Completed smoke task](../../tasks/done/real-gitlab-strategy-single-smoke.md)
records source versions, receipts and the archive path.
