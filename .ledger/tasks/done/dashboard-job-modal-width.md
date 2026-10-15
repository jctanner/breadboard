# Widen dashboard job details

Replace the job detail modal's fixed 80rem cap with a width 10% narrower than
the page container. The page uses 90% of the viewport, so the dialog should use
81vw, retaining 1rem side gutters on mobile. Work on `main`.

Completed directly on `main`. The dialog is 81vw on larger screens and keeps
the previous 1rem mobile side gutters at 640px and below.

Verification:

- Flask test client renders `/jobs` successfully with the new modal CSS.
- `git diff --check` passed.
- `make host-rebuild-dashboard` and deployment rollout completed; new pod uses
  image `sha256:107ca795c903970733f579aaa497e08607d942c8be058fec9c769628c205cf50`.
- Playwright opened an actual historical seed job at `dashboard.local/jobs`.
  At 3,840px, the dialog is 3,110px wide versus the page's 3,456px (90%),
  up from the previous 1,280px cap. At 1,920px and 1,280px, it remains 90%
  of page width. At 640px and 390px, it retains 16px side gutters.
- The deployed dialog opens and closes correctly and stays within the viewport
  at all five checked sizes. No jobs were submitted or changed.
