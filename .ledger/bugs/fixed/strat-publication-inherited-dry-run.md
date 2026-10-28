# Ambient DRY_RUN changes validated publication classification

PR #85 comment 4380483700. prepare_publication passes its environment to the
extractor, whose argparse default treats any nonempty DRY_RUN (including 0)
as true. A validated live publication can therefore produce dry-run metadata
and disappear from production summaries.

Reproduced using the actual skip-only publication/extraction path with
DRY_RUN=0 and DRY_RUN=1. Local repair removes only that legacy environment
variable in the extractor child; the validated result supplies --dry-run.
The dry-run control remains true. Fixed in 2ecd758, published in PR #85 head
b8d67c3. Combined full suite: 1,362 pass, six optional skips. Evidence is sealed
under var/run-data/20261026-strat-pr85-review-and-merge/.
