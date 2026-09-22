#!/usr/bin/env python3
"""Seed the trust-boundary check that breakpoint B4 asks for.

B4 asks for a workflow job that shows its OIDC claims, exchanges them at the
mint, and gets a credential that works on its own repository and is refused on
another. The exchange and the working credential were already demonstrable from
an ordinary triage run; the claims were not, because the log masks the token,
and the refusal was covered by unit tests rather than shown.

This seeds both halves:

- a private repository the agent roles are not collaborators on, so "another
  repository" is a real thing rather than a hypothetical; and
- a workflow that prints the token's own claims, performs the exchange, and
  then probes the boundary in both directions.

The workflow asserts rather than narrates. Every probe has an expected status
and fails the job when it does not match, so a boundary that quietly stops
holding shows up as a red run instead of a paragraph nobody rereads.

The last step probes the endpoints that used to leak. Repository metadata was
once the only one that checked visibility at all, so the others are where a
regression would appear first, and asserting them keeps the boundary honest
rather than taking the front door's word for it. That leak was G22, fixed on
2026-09-21; this step is what keeps it fixed.
"""

from __future__ import annotations

import base64
import sys

from emulator import ORG, REPO, api_request


OFF_LIMITS = "off-limits"
WORKFLOW_PATH = ".github/workflows/fullsend-trust-check.yaml"

WORKFLOW = """# Seeded by deploy/fullsend/seed/seed-trust-check.py for breakpoint B4.
# Not part of Fullsend. This exists to make the trust boundary observable.
name: Fullsend trust check

on:
  workflow_dispatch:

permissions:
  contents: read
  id-token: write

jobs:
  trust:
    name: Trust boundary
    runs-on: fullsend
    env:
      MINT_URL: ${{ vars.FULLSEND_MINT_URL }}
      OWN_REPO: ${{ github.repository }}
      OTHER_REPO: OWNER/OFF_LIMITS
    steps:
      - name: Show this job's OIDC claims
        shell: bash
        run: |
          set -euo pipefail
          ASSERTION=$(curl -sSf \\
            -H "Authorization: bearer $ACTIONS_ID_TOKEN_REQUEST_TOKEN" \\
            "${ACTIONS_ID_TOKEN_REQUEST_URL}&audience=fullsend-mint" | jq -r '.value')
          echo "::add-mask::$ASSERTION"
          echo "$ASSERTION" > "$RUNNER_TEMP/assertion.jwt"
          echo "The claims this job can prove about itself:"
          python3 - "$ASSERTION" <<'PY'
          import base64, json, sys
          payload = sys.argv[1].split(".")[1]
          payload += "=" * (-len(payload) % 4)
          claims = json.loads(base64.urlsafe_b64decode(payload))
          shown = [
              "iss", "aud", "sub", "repository", "repository_owner",
              "repository_id", "workflow", "workflow_ref", "job_workflow_ref",
              "ref", "sha", "event_name", "actor", "run_id", "run_attempt",
              "runner_environment",
          ]
          width = max(len(k) for k in shown)
          for key in shown:
              print(f"  {key:<{width}}  {claims.get(key, '(absent)')}")
          PY

      - name: Exchange the assertion for a scoped credential
        shell: bash
        run: |
          set -euo pipefail
          ASSERTION=$(cat "$RUNNER_TEMP/assertion.jwt")
          echo "::add-mask::$ASSERTION"
          RESPONSE=$(curl -sSf \\
            -H "Authorization: Bearer $ASSERTION" \\
            -H "Content-Type: application/json" \\
            -d "{\\"role\\":\\"triage\\",\\"repos\\":[\\"${OWN_REPO##*/}\\"],\\"level\\":\\"write\\"}" \\
            "${MINT_URL}/v1/token")
          echo "::add-mask::$RESPONSE"
          CREDENTIAL=$(echo "$RESPONSE" | jq -r '.token')
          echo "::add-mask::$CREDENTIAL"
          echo "$CREDENTIAL" > "$RUNNER_TEMP/credential"
          echo "The mint granted:"
          echo "$RESPONSE" | jq -r '"  repos        " + (.granted_repos | join(","))'
          echo "$RESPONSE" | jq -r '"  permissions  " + (.granted_permissions | to_entries | map("\\(.key)=\\(.value)") | join(","))'
          echo "$RESPONSE" | jq -r '"  selection    " + .repository_selection'
          echo "$RESPONSE" | jq -r '"  subject      " + .subject'

      - name: The mint refuses to mint for another repository
        shell: bash
        run: |
          set -euo pipefail
          ASSERTION=$(cat "$RUNNER_TEMP/assertion.jwt")
          echo "::add-mask::$ASSERTION"
          BODY=$(mktemp)
          STATUS=$(curl -s -o "$BODY" -w '%{http_code}' \\
            -H "Authorization: Bearer $ASSERTION" \\
            -H "Content-Type: application/json" \\
            -d "{\\"role\\":\\"triage\\",\\"repos\\":[\\"${OTHER_REPO##*/}\\"],\\"level\\":\\"write\\"}" \\
            "${MINT_URL}/v1/token")
          echo "  asked for   ${OTHER_REPO}"
          echo "  status      ${STATUS} (expected 403)"
          echo "  reason      $(jq -r '.error // "(none)"' < "$BODY")"
          test "$STATUS" = "403" || {
            echo "::error::the mint minted a credential for a repository this run is not for"
            exit 1
          }

      - name: No credential this job never asked for is present
        shell: bash
        run: |
          set -euo pipefail
          # This is the step that would have caught G39.
          #
          # Everything above authenticates with an explicit Authorization
          # header, which is the one way of calling the forge that cannot be
          # influenced by the environment. Agents do not work that way: they
          # run gh, and gh picks its credential from an environment variable.
          # If the runner puts a broader credential in that variable, every
          # call an agent makes is made with the broader credential and
          # nothing in the log says so - the mint still succeeds, the scoped
          # token is still issued, and it is simply never used.
          #
          # GitHub puts no credential in a step's environment unless the
          # workflow asks for one. This job asks for none, so all four must be
          # empty.
          LEAKED=""
          for VAR in GH_TOKEN GITHUB_TOKEN GH_ENTERPRISE_TOKEN GITHUB_ENTERPRISE_TOKEN; do
            VALUE="$(printenv -- "$VAR" || true)"
            if [ -n "$VALUE" ]; then
              LEAKED="${LEAKED} ${VAR}"
              echo "  ${VAR} is set, and this job never asked for it"
            else
              echo "  ${VAR} is unset, as it should be"
            fi
          done
          test -z "$LEAKED" || {
            echo "::error::the runner put a credential in this step that the workflow never requested:${LEAKED}"
            exit 1
          }

      - name: gh sends the minted credential, not something broader
        shell: bash
        run: |
          set -euo pipefail
          CREDENTIAL=$(cat "$RUNNER_TEMP/credential")
          echo "::add-mask::$CREDENTIAL"
          # gh selects its credential by host: GH_TOKEN on github.com,
          # GH_ENTERPRISE_TOKEN anywhere else. Set both, which is what a tool
          # scoping a freshly minted token has to do to be certain gh reads
          # the one it just minted.
          export GH_HOST="${GH_HOST:-$(echo "${GITHUB_SERVER_URL}" | sed -e 's#^https://##' -e 's#^http://##' -e 's#/.*$##')}"
          export GH_TOKEN="$CREDENTIAL"
          export GH_ENTERPRISE_TOKEN="$CREDENTIAL"

          # The positive half matters as much as the negative one: without it
          # a refusal below could mean gh had no usable credential at all,
          # which would pass this check while proving nothing.
          gh api "repos/${OWN_REPO}" --jq '.full_name' > /dev/null
          echo "  gh api repos/${OWN_REPO} -> ok"

          if gh api "repos/${OTHER_REPO}" > /dev/null 2>&1; then
            echo "::error::gh reached a repository the minted credential cannot: it is authenticating as something else"
            exit 1
          fi
          echo "  gh api repos/${OTHER_REPO} -> refused, as it should be"

      - name: The credential works on its own repository
        shell: bash
        run: |
          set -euo pipefail
          CREDENTIAL=$(cat "$RUNNER_TEMP/credential")
          echo "::add-mask::$CREDENTIAL"
          STATUS=$(curl -s -o /dev/null -w '%{http_code}' \\
            -H "Authorization: token $CREDENTIAL" \\
            "${GITHUB_API_URL}/repos/${OWN_REPO}")
          echo "  GET /repos/${OWN_REPO} -> ${STATUS} (expected 200)"
          test "$STATUS" = "200" || {
            echo "::error::the minted credential does not work on its own repository"
            exit 1
          }

      - name: The credential is refused on another repository
        shell: bash
        run: |
          set -euo pipefail
          CREDENTIAL=$(cat "$RUNNER_TEMP/credential")
          echo "::add-mask::$CREDENTIAL"
          STATUS=$(curl -s -o /dev/null -w '%{http_code}' \\
            -H "Authorization: token $CREDENTIAL" \\
            "${GITHUB_API_URL}/repos/${OTHER_REPO}")
          echo "  GET /repos/${OTHER_REPO} -> ${STATUS} (expected 404)"
          test "$STATUS" = "404" || {
            echo "::error::a private repository this role cannot reach was served"
            exit 1
          }

      - name: The refusal holds past the first endpoint
        shell: bash
        run: |
          set -euo pipefail
          CREDENTIAL=$(cat "$RUNNER_TEMP/credential")
          echo "::add-mask::$CREDENTIAL"
          # Repository metadata was the only endpoint that ever checked
          # visibility. These are the ones that did not, and a regression here
          # means "private" has stopped meaning anything past the front door.
          for SUFFIX in issues contents/README.md commits branches labels; do
            STATUS=$(curl -s -o /dev/null -w '%{http_code}' \\
              -H "Authorization: token $CREDENTIAL" \\
              "${GITHUB_API_URL}/repos/${OTHER_REPO}/${SUFFIX}")
            echo "  GET /repos/${OTHER_REPO}/${SUFFIX} -> ${STATUS} (expected 404)"
            test "$STATUS" = "404" || {
              echo "::error::${SUFFIX} served a private repository this role cannot reach"
              exit 1
            }
          done
"""


def ensure_off_limits() -> str:
    """A private repository none of the agent roles collaborate on."""
    full_name = f"{ORG}/{OFF_LIMITS}"
    status, _ = api_request("GET", f"/repos/{full_name}")
    if status == 200:
        return full_name
    status, payload = api_request(
        "POST",
        f"/orgs/{ORG}/repos",
        {
            "name": OFF_LIMITS,
            "private": True,
            "auto_init": True,
            "description": "Conformance: a repository the agent roles must not reach",
        },
    )
    if status not in (201, 422):
        raise RuntimeError(f"create {full_name} failed: HTTP {status}: {payload}")
    return full_name


def put_workflow(other_repo: str) -> None:
    content = WORKFLOW.replace("OWNER/OFF_LIMITS", other_repo)
    encoded = base64.b64encode(content.encode()).decode()
    body = {
        "message": "Seed the B4 trust-boundary check",
        "content": encoded,
        "branch": "main",
    }
    status, existing = api_request(
        "GET", f"/repos/{ORG}/{REPO}/contents/{WORKFLOW_PATH}"
    )
    if status == 200 and isinstance(existing, dict):
        if existing.get("content", "").replace("\n", "") == encoded:
            print(f"trust check already current at {ORG}/{REPO}:{WORKFLOW_PATH}")
            return
        body["sha"] = existing["sha"]
    status, payload = api_request(
        "PUT", f"/repos/{ORG}/{REPO}/contents/{WORKFLOW_PATH}", body
    )
    if status not in (200, 201):
        raise RuntimeError(f"write {WORKFLOW_PATH} failed: HTTP {status}: {payload}")
    print(f"seeded trust check at {ORG}/{REPO}:{WORKFLOW_PATH}")


def main() -> None:
    other = ensure_off_limits()
    print(f"off-limits repository: {other} (private, no agent collaborators)")
    put_workflow(other)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as exc:
        sys.exit(f"Trust check seed failed: {exc}")
