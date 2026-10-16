# Repair mixed-state recovery and run one Opus test

User authorized fixing the failures from markov-run-eaf92e4d and then one
claude-opus-4-6 test. This authorizes the Opus pass directly after local
validation; no extra paid GLM iteration is planned.

- [x] Restore verified review-only import status before scoring/review hashes.
- [x] Reject unverified promotion and preserve existing reviewed inputs.
- [x] Send the full seed report through stdin instead of one exec argument.
- [x] Prevent a failed native Workflow from entering parent-led repair/relaunch.
- [x] Regress the actual Draft import and final validation without inference.
- [x] Run required component suite and offline benchmark/monitor checks.
- [ ] Publish exact commits, sync Markovd and verify prior archive receipts.
- [ ] Launch one mixed-state Opus pass, cap ten, one iteration, retain evidence.

Earlier GLM capture is complete, independently verified and has a final receipt:
var/run-data/strat-workflow-hardening/fullsend-glm-mixed-state-c10-20261015/
markov-run-eaf92e4d/20261016T012038554137Z.

The fixture still has 29 initial issues, ten discovery candidates, nine acquired
(four fresh, three refine, two review-only), one late human skip and one deferred.
Keep earlier benchmark pins/results and numeric-only approval unchanged.

Candidate f5691f7e01b392be6b177356dbf204918a1b42af is published. Full suite
1,041 passed / six skipped; focused recovery 57 passed; benchmark 96 checks
passed (one optional test skipped), separate real local Jira suite nine passed.
Logs: /tmp/strat-mixed-opus-full-tests-final.log,
/tmp/strat-mixed-opus-benchmark-tests.log,
/tmp/strat-mixed-opus-local-integration.log. No inference in these checks.
