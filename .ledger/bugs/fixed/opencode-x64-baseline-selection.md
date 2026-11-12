# Select the conservative OpenCode x64 artifact explicitly

A version-only smoke on a non-AVX2 host cannot cover all later instruction paths.
Select the build script's x64-baseline artifact on x86_64, retain arm64 on aarch64,
and reject unsupported architectures before compiling. The source's --baseline
option may emit other artifacts too; only the selected glibc artifact is copied.

The selected baseline builds on the non-AVX2 target. As pipelineagent, the final
image runs OpenCode version and configuration resolution with its MLflow plugin
configured, verifies internal HTTPS from Node, and runs pipeline CLI help. Interactive
TUI and real model inference remain outside this smoke test.
