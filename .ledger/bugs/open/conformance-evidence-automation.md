# Automate additional conformance provenance checks

Nonblocking follow-up accepted during final review. The current shell harness
selects a recent issues-triggered run without explicitly binding it to the filed
issue, and checks the agent's successful-exit marker without itself parsing every
behaviour operation from the artifact. General concurrent-run selection and
structured artifact assertions should be hardened separately.

The current qualification is not relying on those gaps: run 9's artifact was
independently checked for 10/10 successful operations and agent/root exits 0/0;
its telemetry work item is fullsend-dev/triage-target#5 and pipeline run is 9,
matching the filed issue/run. Specific issue comments/labels have the minted
triage-bot identity. Existing strict checks were retained and caught the earlier
missing-file scenario failure despite a green workflow. No additional source
changes are needed to establish this audited run's result.

Also retain the sandbox pod imageID before cleanup in future runs. Current pod
metadata was deleted normally; per-image local IDs and exact policy hashes are
recorded, with no image rebuild/tag changes during the run or audit. The archive
itself is now fingerprinted, and its workflow-head scenario is checked against
the committed render. Distinguish source metadata captured at evidence collection
from the emulator target repository's workflow checkout SHA.
