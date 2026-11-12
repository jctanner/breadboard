# Unattended Fedora Podman cannot resolve the Bun builder image

## Reproduction

PR #10 fresh deployment on Fedora 44 with Podman's enforcing short-name policy.
The pipeline-agent build reaches the OpenCode stage and fails:
`short-name resolution enforced but cannot prompt without a TTY`.

## Fix

Qualify the existing builder image as `docker.io/oven/bun:1.3.14-debian`, preserving
its version and Docker Hub source without changing host-wide registry policy.

## Validation

Dockerfile whitespace check passes. The resumed remote image build pulled the
qualified image successfully and advanced into the OpenCode source/build stage,
proving the short-name failure is resolved without weakening registry policy.
