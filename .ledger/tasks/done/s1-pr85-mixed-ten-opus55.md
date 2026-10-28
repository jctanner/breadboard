# Repeat the mixed-state ten-ticket batch with Opus 5.5

User authorized 2026-10-18: one repeat of the passing mixed-state ten-ticket
S1 batch, using claude-opus-5-5. Keep candidate 6ed858b, the existing distinct
fixture, high effort, concurrency ten, one iteration and model-free repeat.
No automatic paid retry or fallback to Opus 4.6/GLM.

- [x] Add a separate model variant/tier while preserving prior benchmark pins.
- [x] Render exact submission offline and verify single S1 selection/model.
- [x] Enable Opus 5.5 on the existing Vertex upstream and verify access.
- [x] Publish benchmark configuration, sync/import through markovd-cli and
      attest the imported files against the published source.
- [x] Verify archives and idle/schedule state, then submit exactly once through
      Markovd/Breadboard and attach the terminal archive observer.
- [x] Verify effective runtime source/model, ten acquisitions and 4/4/2 split
      from retained evidence; late live process inspection missed the primary.
- [x] Analyze final outcome, model-free repeat and verified archive.

The unchanged fixture has 29 initial issues: eighteen distinct RFE subjects,
four fresh, four refinement and two verified review-only acquisitions, plus
eight controls. Expect four clones, eight refinement/push paths, ten reviews
and forty assessments; preserve controls/review-only state and release locks.
Repeat acquires nothing, skips the human-only control, exits 78 and uses no
model calls.

Prior comparison run: markov-run-bfc0b766, clean PASS in 30m07s with complete,
independently verified archive. Runtime image/Claude version stay pinned to the
qualified configuration where possible; record any necessary change explicitly.
The run remains Breadboard/Markovd/Kubernetes qualification, not Fullsend/OpenShell
or independent strategy-content judging.

Preparation finding: vertex-strat-evals is ready with Google service-account
authentication, global region. Its explicit relay inventory currently omits
Opus 5.5; adding that exact model is necessary before the requested run.

## Published preparation

Breadboard 0b890213a1c5defad3c2ad5df50f8353e2d3bfdc is pushed on main.
Only five benchmark files are committed; unrelated ledger/CLI changes are
excluded. Variant opus55 maps exactly to claude-opus-5-5; tier
s1-pr85-mixed-ten-opus55 retains the previous tier's source, fixture and settings.
Offline suite: 109 tests run, 107 pass, two optional isolated-emulator checks
skip. Real Markov exact-payload simulation and directory validation pass;
staged redacted Gitleaks scan and diff check pass. All 81 imported files match
the published source.

The Vertex provider inventory was updated with optimistic version checking,
preserving its three existing models. One availability probe through the
jobs' existing relay ADC/project credentials returns HTTP 200 and the exact
claude-opus-5-5 response model (14 input tokens, one output token). No upstream
credential was printed or written to source. Probe/inventory evidence is saved
in the new campaign's launch-context before batch submission.

Controller: /tmp/s1-opus55-mixed.py, with a durable copy for the terminal
read-only observer. Campaign:
var/run-data/strat-workflow-hardening/pr85-mixed-ten-vertex-opus55-20261018/.

## Terminal result; archive verified

Submitted once as markov-run-296d9e2e at 21:34:24 UTC. Both retained prior
archives independently reverified before the reset. Detached observer 1071434
is attached and cannot submit replacement work. Model job cf6af9 completed
21:34:56–22:00:14 UTC, 25m18s; native Workflow 23m19s. All pipeline stage exits
are zero, all ten mixed-state paths complete, controls/locks/repeat pass.

Pinned benchmark FAIL solely for one scope-report format false negative. All
forty selected reports independently match their receiving channel, producer,
provenance hash and composed review. There are 42 specialist launches, including
two additional testability calls. The actual report and original FAIL stay
unchanged. No checker fix, model retry or new batch has been launched.

All 791 requests use Opus 5.5; 37,261,081 accounted tokens, $42.80 CLI list-price
equivalent, no recorded API/rate errors. Source script, Claude version and image
match the intended candidate/runtime. The process inspection happened after
completion, so source/model evidence is retrospective, not a captured live PID.

[Analysis and comparison](../../notes/s1-opus55-mixed-ten-20261018.md).
Archive completed at 22:20:26 UTC: 13,930 files / 18,848,434,120 bytes,
complete/final, errors=[]. Independent checksum verification passes and final
receipts are published. All 791 captured generation responses uniquely join
successful, complete, non-synthetic Vertex telemetry records on vertex-strat-evals
with Google service-account authentication and the exact requested model.
The capture also records 52 count-token operations and one separate small
non-stream generation; these are not added to the job's captured-generation
usage totals. Independent analysis and its checksum manifest are retained in
the campaign's separate analysis/ directory. Task complete; the original
benchmark FAIL remains explicit. The parser bug was subsequently repaired
without another model run; [scope-checker follow-up](strat-review-scope-subject-checker.md).
