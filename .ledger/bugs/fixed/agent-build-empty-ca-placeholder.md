# Agent builds silently accepted missing CA input

Both agent image build entry points previously wrote an empty CA placeholder after
ConfigMap extraction failed. The image could build without trust for internal TLS,
and optional tag-only reuse could then retain it.

Fail closed on unavailable/empty/invalid CA input, require OpenSSL explicitly,
serialize only the public X509 certificate (discard appended PEM material), and
clean the generated context certificate on every exit. The image validates its
certificate too. Portable RUN chmod steps keep public certificates readable without
requiring Docker BuildKit. Document forced rebuilds when upgrading old images.

Ten offline tests cover both entry points with unavailable, empty, invalid, valid
and appended-private-key input. They assert engine invocation, exact public-only
certificate content and cleanup even when the engine fails. The focused suite has
68 passes and five live skips. The target's final image verifies custom-domain
HTTPS from Node as its non-root runtime user.
