# Fresh role installations had empty grants

The first conformance run reached Mint but received422 when requesting triage
permissions. Secret-free audit counters and whitelisted API metadata isolated the
cause: the UI App inventory omits permissions. Bootstrap read that inventory and
explicitly installed an empty permission map.

Read canonical role grants from the permissions-bearing REST App record; use the
UI inventory only for selection reconciliation. Refuse missing/empty/malformed
metadata before writes, verify returned installation grants, and best-effort delete
only a newly created mismatched installation. Do not delete existing operator
installations on verification failure. curl/Python now verify the selected public
CA; no TLS bypass remains. Regression tests vary all eight role maps, cover old
selected installations and empty/malformed/mismatched responses, and assert TLS.

The real bootstrap succeeds. Authenticated read-only checks inside Mint confirm
all eight installation maps match canonical role grants without exporting keys,
JWTs or tokens. The subsequent conformance run passes mint, checkout and setup,
but is blocked later at OpenShell configuration activation. Bootstrap remains a
non-atomic sequence across eight Apps; a later failure does not roll back earlier
valid reconciliations. Mint still downscopes every issued token by role.

A further review added equality against the exact requested bootstrap permissions,
not only the REST App response. The shell accumulates the eight ensure_app inputs
and the Python verifier rejects a broader server App map before installation
writes. Also validate inventory entry types/positive IDs and require returned
repository_selection=all. Tests cover broader App grants, malformed inventory and
selected installations as well as distinct old/new rollback IDs and cleanup
network errors.
