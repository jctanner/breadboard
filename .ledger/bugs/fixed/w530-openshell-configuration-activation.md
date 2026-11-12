# OpenShell rejected the pinned image policy

## Status

Fixed by f349aaf; qualified on W530 with both final images and strict Fullsend
conformance run 9. Ready for manual merge; no merge was performed.

## Cause and repair

The harness-pinned Fullsend base policy contains tls: terminate, which the pinned
OpenShell 0.1.4 rejects. Its empty/default TLS value means automatic termination.
The build helper reads the public policy from the exact pinned image without
starting it and edits only the obsolete scalar values. Unrelated bytes, policy
rules and CA trust remain intact. Archive members are bounded and checked without
extracting image links onto the host. Named temporary containers and volumes are
removed, and the generated policy is installed root-owned mode 0644.

## Validation

Both sandbox and code images contain their independently generated expected policy
and automatically reach ConfigurationAccepted/Ready. Code execution through the
boundary succeeds. Verified HTTPS GET returns 200. A provider-free A/B/A test
returns POST 403 under read-only, origin 405 under read-write, then 403 again when
read-only is restored. Diagnostic sandboxes were removed. Conformance run 9 passes
all 10 operations, both recorded exit codes are 0, and labels/comments use the
minted triage bot. Cluster, certificate and DNS checks pass.

See ../../notes/cc61-w530-final-evidence.json for image IDs, immutable base digests,
policy hashes, issue/run binding and startup timing. Temporary disk use during
trusted image cp remains an accepted follow-up: limits apply before parsing but
after copying; future untrusted images should impose an in-flight disk bound.
