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

## Authorized 2026-10-16

The user approved fixing the historical signoffs, including the described
history rewrite and force-push with lease. Preserve the old tip, existing
author credit and source trees, then verify DCO on the published replacement.

## Completed

Repaired the 15 missing Signed-off-by trailers using the original committer's
identity, jctanner <tanner.jc@gmail.com>, which the upstream DCO checker accepts
for the automation-authored commit too. No author identity was changed or
other author's signoff fabricated. All original author/committer dates and
file trees are preserved. gsun's eight commits and merge 46cb96e are untouched.

- Old tip: f941955b343b985fa8ae22f7c3e321899a3aa588.
- New tip: 18cdf46716a291439e766d9341eb8e0a03702d52.
- Local and fork backup: backup/pr85-before-dco-20261016-f941955.
- Sixteen commits acquire new hashes: fifteen changed messages and the final
  already-signed commit whose parent changed.
- All 24 non-merge PR commits have a matching author/committer signoff.
- Every rewritten commit's tree matches its original; final tree remains
  b0bef2fe7970f6b6c0e0484192f9ebae2afaa8c0. git diff and diff --check pass.
- Exact force-with-lease required the old published tip; push succeeded.
- GitHub DCO result: success, "All commits are signed off!"

Existing test results apply to the identical source tree. No model calls or
new local runtime test rounds were needed. GitHub reran CI on the new hashes: Python 3.11 and 3.12 tests, lint and
Unicode checks all passed. All 21 review threads remain resolved.
Historical benchmark pins and archived pre-repair records remain unchanged;
the remote backup keeps those commits reachable.

## Commit mapping

| Original | Repaired | Signoff added |
| --- | --- | --- |
| db42db05ce2eb1b60e89a84e95386f745fcc096c | c8077384284bbbaecd470b26826304c90149c359 | yes |
| 37674fe16845d9bdb88b164fb2d67db58dd6028e | 023179d56ee09107a8e37a4ce5b03f15855c4470 | yes |
| b804d7c593ea253a582fb4c94b2da92d966cc9ca | a31dfb4dab89b1f667d5444a269588cbd2750618 | yes |
| 248c388608364e8ed82f1febb967267f6181452e | 6ac0ef4f6b67c81d08be4f3a36125e9cf735dd05 | yes |
| 7b3b9cec240812b81ed3a528eacfc2c57673a773 | 5d665c72368de01a3ecdf6e35af28f2611169beb | yes |
| deaed7b014e397a9331b782f6317a43057498b8d | 591a3065f7fec40dc4a78520abd80f94554b20b1 | yes |
| 4eac463757e3c2d33046aa3342585d5725e00dd3 | 35ad75d6776538711290286f5fb1a1be16445e57 | yes |
| e49b02d6c522476aaf471d7842bebaac24a3dfd2 | afb1d2ccb2123f25d4c69c67461a0cc052aebbe6 | yes |
| 1af9ec2719f08e564351dc2b1f23c061a7a12738 | a8cfc87a39e4da86403d7316233640e2b1a9bca5 | yes |
| 4bc406d678403f01449eab8bddd46ebd1417221f | de8226ad2dcfe3435ee61b655e670373b01f9f5b | yes |
| 1f594d0bbb6e43fb6fca8c94e767857b9dd2ab5c | 0ab2dc125762e67b46881d4916777bcab058efb1 | yes |
| d5817e7d2a2e063e191d7ea7161631876dd0c11a | 2d204bfeb14725d912534fc544f86fa7697eefe7 | yes |
| 6a05210215247b287bb0fb61ed02e423c9de8692 | 4bff2cbeb9dc60af2cdf73af0c44e93766a4c416 | yes |
| fbc335bedb4a4eb97265da89d36bc29009a41fde | 806f6a1dff97fb56e47d2a815d22ab984b817918 | yes |
| f5691f7e01b392be6b177356dbf204918a1b42af | 1bc4978db62eb7e38b8e082c5125e81632536548 | yes |
| f941955b343b985fa8ae22f7c3e321899a3aa588 | 18cdf46716a291439e766d9341eb8e0a03702d52 | existing |
