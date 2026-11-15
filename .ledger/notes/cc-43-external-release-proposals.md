# CC-43: Release proposals for repositories owned outside jctanner

No writes, branches, tags or releases were made in these repositories.

## vokramd/markov

Preserve existing SemVer: v0.1.0 is a published GitHub release and v0.2.0 is
an existing git tag. The checkout has a GoReleaser release-candidate workflow
triggered by v* tags with archive, package and OCI candidate validation. Do
not replace it with CalVer or duplicate CC-71 work.

## vokramd/markovd

Go API and React frontend; Dockerfile builds both and serves HTTP on 8080;
/health is the smoke endpoint. No tags, releases or workflow files were
observed. Coordinate its release version contract with Markov/CC-71 before
adding anything: prefer retaining its owner's chosen scheme, potentially
v-prefixed SemVer aligned with Markov, rather than imposing CalVer.
Suggested CI: Go tests and UI build, then Linux amd64 image build and /health
smoke test. Publish tested images and digest-backed GitHub releases only
after explicit authorization to change vokramd repositories.

## opendatahub-io/observatory

Python FastAPI and React; multi-stage Dockerfile, port 8000, /healthz.
No tags/releases or workflow files observed. Proposed CI: backend tests on
SQLite, frontend build/tests, container smoke test and GHCR publication.
Determine release policy with repository owners before adopting CalVer.
The current integration Dockerfile copies org-pulse-config.json; confirm
this is committed and contains no deployment-specific credentials before
publishing. External repository writes require separate approval.
