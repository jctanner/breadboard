# Agent builds silently accepted missing CA input

Both agent image build entry points previously wrote an empty CA placeholder after
ConfigMap extraction failed. The image could build without trust for internal TLS,
and optional tag-only reuse could then retain it.

Fail closed on unavailable/empty/invalid CA input, require OpenSSL explicitly,
serialize only the public X509 certificate (discard appended PEM material), and
clean the generated context certificate on every exit. The image validates its
certificate too. Portable RUN chmod steps keep public certificates readable without
requiring Docker BuildKit. Document forced rebuilds when upgrading old images.

Forty-eight offline cases cover both entry points and absolute/relative roots with unavailable, empty, invalid, valid
appended/prepended-private-key and standard/legacy/trusted multi-certificate bundle input. They assert engine invocation, exact public-only
certificate content and cleanup even when the engine fails. The focused suite has
106 passes and five live skips. The target's final image verifies custom-domain
HTTPS from Node as its non-root runtime user.

Require exactly one certificate rather than silently discarding a bundle. Canonicalize
the project root and retain an absolute cleanup path across later directory changes.

README validation claims are limited to parseability and public serialization;
expiry and CA policy remain deployment-validation responsibilities. The real
cluster ConfigMap passes the final entry point to a substituted engine boundary,
and a forced engine failure removes the context file with the expected CA fingerprint.

Corrupt DER inside valid PEM armor reaches the OpenSSL failure branch. Tests also
reject standalone legacy/trusted labels and assert the intended operator error
message, engine isolation, exact certificate output and cleanup.
