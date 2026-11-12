# Fresh Fullsend seed failed ownership and transient database checks

The isolated Git environment correctly disables global configuration, but that
also discarded the service's narrow trusted-checkout list under sudo. Give each
Git call a temporary global config containing only the controlled resolved path,
then delete it. Disable hooks, fsmonitor, credential helpers and ext transport.
Retain default TLS verification and the explicit public CA. Ownership and hook
regressions use real local Git and prove no persistent trust remains.

The real seed later received503/sqlite_locked with the emulator's explicit retry
message. Retry at most four times (1/2/4s backoff) only on that response and
idempotent methods or unique-name org/repository creation. Do not replay arbitrary
POSTs, auth/non-lock failures or the explicit unsafe-replay response. Confirm422
conflicts by GET; repository confirmation requires a default branch. Tests cover
those branches and exhaustion. The complete real seed subsequently succeeded.

Operator-owned local Git config remains within the operator's existing sudo trust
boundary; URL-specific local TLS settings and other local config are not globally
sanitized. Seed remotes are created in controlled temporary repositories. Ancient
Git versions without GIT_CONFIG_GLOBAL are not qualified; current supported host
versions work, and ownership rejection fails safely rather than broadening trust.
