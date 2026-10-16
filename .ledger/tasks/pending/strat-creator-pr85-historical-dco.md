# PR 85: historical DCO signoffs

The DCO check on feature head f5691f7 reported 15 unsigned historical commits.
The remediation commit f941955 is signed off. Default code and native controls
pass; this process check is independent of benchmark results.

Do not silently rewrite published commit identities or attest for another
author. The branch includes benchmark pins and an automation-authored commit.
The upstream repository has no .github/dco.yml remediation policy configured.

Before any history repair, obtain the user's certification and explicit
authorization for the exact rewrite/force push. Preserve the old tip with a
backup reference and record old/new commit mapping. The alternative is a
maintainer-approved DCO remediation policy or merge process. No force push has
been performed.

[Implementation remediation](../done/strat-creator-pr85-remediation.md).
