#!/usr/bin/env python3
"""Replace the triage target fixtures with the Fullsend shim topology.

The target repository contains only the managed event shim.  The separate
``.fullsend`` repository contains the dispatcher, thin stage callers, and the
agent workflow implementations.  This mirrors the production workflow-call
layout and keeps stage routing centralized.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.parse import quote

from m1_seed import API_URL, ORG, REPO, TOKEN, api_request, ensure_org, ensure_repo, run_git
from m10_seed import files_to_push as m10_review_files
from m9_seed import APP_ACTION, _copy, files_to_push as m9_files


CONFIG_REPO = ".fullsend"
TARGET_WORKFLOW = ".github/workflows/fullsend.yaml"
CONFIG_DISPATCH = ".github/workflows/dispatch.yml"
CONFIG_TRIAGE = ".github/workflows/triage.yml"
CONFIG_TRIAGE_AGENT = ".github/workflows/triage-agent.yml"
CONFIG_CODE = ".github/workflows/code.yml"
CONFIG_CODE_AGENT = ".github/workflows/code-agent.yml"
CONFIG_REVIEW = ".github/workflows/review.yml"
CONFIG_REVIEW_AGENT = ".github/workflows/review-agent.yml"
CONFIG_FIX = ".github/workflows/fix.yml"
CONFIG_FIX_AGENT = ".github/workflows/fix-agent.yml"


SHIM_WORKFLOW = r'''---
# This file is managed by Fullsend. Do not edit it directly.
# Development mirror of the production workflow-call shim.
name: fullsend

on:
  issues:
    types: [opened, edited, labeled]
  issue_comment:
    types: [created]
  pull_request_target:
    types: [opened, synchronize, ready_for_review, closed, labeled, unlabeled]
  pull_request_review:
    types: [submitted]

permissions: {}

jobs:
  dispatch:
    concurrency:
      group: >-
        fullsend-dispatch-${{ github.event.issue.number || github.event.pull_request.number }}-${{
          github.event.action == 'labeled' && format('label-{0}', github.event.label.name) || 'dispatch'
        }}
      cancel-in-progress: false
    if: >-
      (github.event_name != 'pull_request_target' && github.event_name != 'pull_request_review'
       || github.event.pull_request.head.ref != 'fullsend/scaffold-install')
      && (github.event_name != 'pull_request_review'
       || github.event.review.user.type != 'Bot'
       || github.event.review.state == 'CHANGES_REQUESTED')
      && (github.event_name != 'issue_comment'
       || github.event.comment.user.type != 'Bot')
      && (github.event.action != 'labeled'
       || startsWith(github.event.label.name, 'ready-'))
    permissions:
      actions: write
      id-token: write
      contents: read
      pull-requests: read
    uses: fullsend-dev/.fullsend/.github/workflows/dispatch.yml@main
    with:
      event_action: ${{ github.event.action }}
'''


DISPATCH_WORKFLOW = r'''---
# fullsend-stage: dispatch
# Central stage router.  The target-repository shim only calls this workflow;
# this workflow selects the stage-specific caller from the event.
name: Dispatch

on:
  workflow_call:
    inputs:
      event_action:
        required: true
        type: string

permissions: {}

jobs:
  dispatch:
    name: Route Fullsend event
    runs-on: [self-hosted, linux, fullsend-router]
    permissions:
      actions: write
      contents: read
      issues: read
      pull-requests: read
      id-token: write
    env:
      GITHUB_API_URL: https://github.local/api/v3
      GITHUB_SERVER_URL: https://github.local
      GH_HOST: github.local
      NO_SSL_VERIFY: "1"
      DISPATCH_REPO: fullsend-dev/.fullsend
      SOURCE_REPO: ${{ github.repository }}
    steps:
      - name: Determine stage
        id: route
        env:
          EVENT_NAME: ${{ github.event_name }}
          # The called workflow retains the caller's event context.  Reading
          # the action from github.event avoids depending on flattened inputs.
          EVENT_ACTION: ${{ github.event.action }}
        run: |
          set -euo pipefail
          stage=""
          label="$(jq -r '.label.name // empty' "${GITHUB_EVENT_PATH}")"
          comment="$(jq -r '.comment.body // empty' "${GITHUB_EVENT_PATH}")"
          needs_info="$(jq -r '[.issue.labels[]? | if type == "object" then .name else . end] | index("needs-info") != null' "${GITHUB_EVENT_PATH}")"
          review_state="$(jq -r '.review.state // empty' "${GITHUB_EVENT_PATH}")"
          case "${EVENT_NAME}:${EVENT_ACTION}" in
            issues:opened|issues:edited)
              stage=triage
              ;;
            issues:labeled)
              case "${label}" in
                ready-for-triage) stage=triage ;;
                ready-to-code) stage=code ;;
                ready-for-review) stage=review ;;
              esac
              ;;
            issue_comment:created)
              case "${comment}" in
                /fs-triage*) stage=triage ;;
                /fs-code*) stage=code ;;
                /fs-review*) stage=review ;;
                /fs-fix*) stage=fix ;;
              esac
              if [[ -z "${stage}" && "${needs_info}" == "true" ]]; then
                stage=triage
              fi
              ;;
            pull_request_review:submitted)
              if [[ "${review_state}" == "CHANGES_REQUESTED" ]]; then
                stage=fix
              else
                stage=review
              fi
              ;;
            pull_request_target:opened|pull_request_target:synchronize|pull_request_target:ready_for_review)
              stage=review
              ;;
            pull_request_target:labeled)
              if [[ "${label}" == "ready-for-review" ]]; then
                stage=review
              fi
              ;;
          esac
          echo "stage=${stage}" >> "${GITHUB_OUTPUT}"
          if [[ -n "${stage}" ]]; then
            echo "Routed to ${stage}"
          else
            echo "No Fullsend stage matched; stopping"
          fi

      - name: Dispatch selected stage workflow
        if: steps.route.outputs.stage != ''
        env:
          EVENT_NAME: ${{ github.event_name }}
          GITHUB_TOKEN: ${{ github.token }}
          STAGE: ${{ steps.route.outputs.stage }}
        run: |
          set -euo pipefail
          payload="$(jq -c . "${GITHUB_EVENT_PATH}")"
          # The emulator's gh compatibility layer does not preserve large
          # workflow_dispatch fields reliably.  Use the Actions API directly;
          # this is also the endpoint used by gh workflow run on GitHub.com.
          token="${GITHUB_TOKEN:-${GH_TOKEN:-}}"
          test -n "${token}"
          request="$(jq -n \
            --arg event_type "${EVENT_NAME}" \
            --arg source_repo "${SOURCE_REPO}" \
            --arg event_payload "${payload}" \
            '{ref:"main",inputs:{event_type:$event_type,source_repo:$source_repo,event_payload:$event_payload}}')"
          curl -kfsS -X POST \
            -H "Authorization: token ${token}" \
            -H 'Content-Type: application/json' \
            -d "${request}" \
            "${GITHUB_API_URL}/repos/${DISPATCH_REPO}/actions/workflows/${STAGE}.yml/dispatches"
'''


TRIAGE_WORKFLOW = r'''---
# fullsend-stage: triage
# Minimal triage stage; retro and prioritize are not seeded.
name: Triage

on:
  workflow_dispatch:
    inputs:
      event_type:
        required: true
        type: string
      source_repo:
        required: true
        type: string
      event_payload:
        required: true
        type: string

concurrency:
  group: fullsend-triage-${{ inputs.source_repo }}-${{ github.run_number }}
  cancel-in-progress: true

jobs:
  triage:
    uses: ./.github/workflows/triage-agent.yml
    with:
      event_type: ${{ inputs.event_type }}
      source_repo: ${{ inputs.source_repo }}
      event_payload: ${{ inputs.event_payload }}
    secrets:
      FULLSEND_GCP_WIF_PROVIDER: ${{ secrets.FULLSEND_GCP_WIF_PROVIDER }}
      FULLSEND_GCP_PROJECT_ID: ${{ secrets.FULLSEND_GCP_PROJECT_ID }}
      OTEL_EXPORTER_OTLP_TRACES_HEADERS: ${{ secrets.OTEL_EXPORTER_OTLP_TRACES_HEADERS }}
'''


TRIAGE_AGENT_WORKFLOW = r'''---
# fullsend-stage: triage-agent
# Development implementation of the reusable Fullsend triage workflow.
name: Triage agent implementation

on:
  workflow_call:
    inputs:
      event_type:
        required: true
        type: string
      source_repo:
        required: true
        type: string
      event_payload:
        required: true
        type: string
    secrets:
      FULLSEND_GCP_WIF_PROVIDER:
        required: false
      FULLSEND_GCP_PROJECT_ID:
        required: false
      OTEL_EXPORTER_OTLP_TRACES_HEADERS:
        required: false

jobs:
  run:
    name: Triage agent
    runs-on: [self-hosted, linux, fullsend]
    permissions:
      contents: read
      id-token: write
      issues: write
    env:
      GITHUB_API_URL: https://github.local/api/v3
      GITHUB_SERVER_URL: https://github.local
      GH_HOST: github.local
      FULLSEND_FORGE: github
      FULLSEND_MINT_URL: http://fullsend-mint-dev.ai-pipeline.svc.cluster.local:8080
      NO_SSL_VERIFY: "1"
      CLAUDE_CODE_USE_VERTEX: "1"
      CLOUD_ML_REGION: global
      GOOGLE_APPLICATION_CREDENTIALS: /var/run/secrets/gcp/credentials.json
      OPENSHELL_GATEWAY_ENDPOINT: http://openshell.openshell-system.svc.cluster.local:8080
      OPENSHELL_GATEWAY_NAME: openshell
      SOURCE_REPO: ${{ inputs.source_repo }}
      EVENT_PAYLOAD: ${{ inputs.event_payload }}
      CODE_ALLOWED_TARGET_BRANCHES: ""
      GIT_BOT_EMAIL: fullsend-code@localhost
    steps:
      - name: Checkout workflow repository
        uses: actions/checkout@v4
        with:
          repository: fullsend-dev/.fullsend
          path: .
          fetch-depth: 1

      - name: Checkout target repository
        uses: actions/checkout@v4
        with:
          repository: ${{ inputs.source_repo }}
          path: target-repo
          fetch-depth: 1

      - name: Mint triage token
        id: app-token
        uses: ./.github/actions/mint-token
        with:
          role: triage
          repos: ${{ inputs.source_repo }}
          mint_url: http://fullsend-mint-dev.ai-pipeline.svc.cluster.local:8080

      - name: Prepare issue context
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
          GITHUB_TOKEN: ${{ steps.app-token.outputs.token }}
        run: |
          set -euo pipefail
          issue_number="$(jq -r '.issue.number // empty' <<<"${EVENT_PAYLOAD}")"
          test -n "${issue_number}"
          issue_url="https://github.com/${SOURCE_REPO}/issues/${issue_number}"
          {
            echo "GITHUB_ISSUE_URL=${issue_url}"
            echo "GITHUB_ISSUE_NUMBER=${issue_number}"
            echo "GH_TOKEN=${GH_TOKEN}"
            echo "GITHUB_TOKEN=${GITHUB_TOKEN}"
            echo "GH_ENTERPRISE_TOKEN=${GH_TOKEN}"
          } >> "${GITHUB_ENV}"

      - name: Run triage agent
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
          GITHUB_TOKEN: ${{ steps.app-token.outputs.token }}
          GH_ENTERPRISE_TOKEN: ${{ steps.app-token.outputs.token }}
          REPO_FULL_NAME: ${{ inputs.source_repo }}
          MINT_REPOS: triage-target
        run: |
          set -eu
          fullsend run triage \
            --fullsend-dir "${GITHUB_WORKSPACE}/.fullsend" \
            --target-repo "${GITHUB_WORKSPACE}/target-repo" \
            --output-dir "${GITHUB_WORKSPACE}/output" \
            --debug=api \
            --forge github
'''


CODE_WORKFLOW = r'''---
# fullsend-stage: code
# Thin caller for the code agent, matching the production .fullsend layout.
name: Code

on:
  workflow_dispatch:
    inputs:
      event_type:
        required: true
        type: string
      source_repo:
        required: true
        type: string
      event_payload:
        required: true
        type: string

jobs:
  code:
    uses: ./.github/workflows/code-agent.yml
    with:
      event_type: ${{ inputs.event_type }}
      source_repo: ${{ inputs.source_repo }}
      event_payload: ${{ inputs.event_payload }}
    secrets:
      FULLSEND_GCP_WIF_PROVIDER: ${{ secrets.FULLSEND_GCP_WIF_PROVIDER }}
      FULLSEND_GCP_PROJECT_ID: ${{ secrets.FULLSEND_GCP_PROJECT_ID }}
      OTEL_EXPORTER_OTLP_TRACES_HEADERS: ${{ secrets.OTEL_EXPORTER_OTLP_TRACES_HEADERS }}
'''


REVIEW_WORKFLOW = r'''---
# fullsend-stage: review
# Thin caller for the review agent, matching the production .fullsend layout.
name: Review

on:
  workflow_dispatch:
    inputs:
      event_type:
        required: true
        type: string
      source_repo:
        required: true
        type: string
      event_payload:
        required: true
        type: string

jobs:
  review:
    uses: ./.github/workflows/review-agent.yml
    with:
      event_type: ${{ inputs.event_type }}
      source_repo: ${{ inputs.source_repo }}
      event_payload: ${{ inputs.event_payload }}
    secrets:
      FULLSEND_GCP_WIF_PROVIDER: ${{ secrets.FULLSEND_GCP_WIF_PROVIDER }}
      FULLSEND_GCP_PROJECT_ID: ${{ secrets.FULLSEND_GCP_PROJECT_ID }}
      OTEL_EXPORTER_OTLP_TRACES_HEADERS: ${{ secrets.OTEL_EXPORTER_OTLP_TRACES_HEADERS }}
'''


FIX_WORKFLOW = r'''---
# fullsend-stage: fix
# Thin caller for the fix agent, matching the production .fullsend layout.
name: Fix

on:
  workflow_dispatch:
    inputs:
      event_type:
        required: true
        type: string
      source_repo:
        required: true
        type: string
      event_payload:
        required: true
        type: string

jobs:
  fix:
    uses: ./.github/workflows/fix-agent.yml
    with:
      event_type: ${{ inputs.event_type }}
      source_repo: ${{ inputs.source_repo }}
      event_payload: ${{ inputs.event_payload }}
    secrets:
      FULLSEND_GCP_WIF_PROVIDER: ${{ secrets.FULLSEND_GCP_WIF_PROVIDER }}
      FULLSEND_GCP_PROJECT_ID: ${{ secrets.FULLSEND_GCP_PROJECT_ID }}
      OTEL_EXPORTER_OTLP_TRACES_HEADERS: ${{ secrets.OTEL_EXPORTER_OTLP_TRACES_HEADERS }}
'''


CODE_AGENT_WORKFLOW = r'''---
# fullsend-stage: code-agent
# Development implementation of the reusable Fullsend code workflow.
name: Code agent implementation

on:
  workflow_call:
    inputs:
      event_type:
        required: true
        type: string
      source_repo:
        required: true
        type: string
      event_payload:
        required: true
        type: string
    secrets:
      FULLSEND_GCP_WIF_PROVIDER:
        required: false
      FULLSEND_GCP_PROJECT_ID:
        required: false
      OTEL_EXPORTER_OTLP_TRACES_HEADERS:
        required: false

jobs:
  run:
    name: Code agent
    runs-on: [self-hosted, linux, fullsend]
    permissions:
      contents: write
      id-token: write
      issues: write
      pull-requests: write
    env:
      GITHUB_API_URL: https://github.local/api/v3
      GITHUB_SERVER_URL: https://github.local
      GH_HOST: github.local
      FULLSEND_FORGE: github
      FULLSEND_MINT_URL: http://fullsend-mint-dev.ai-pipeline.svc.cluster.local:8080
      NO_SSL_VERIFY: "1"
      CLAUDE_CODE_USE_VERTEX: "1"
      CLOUD_ML_REGION: global
      GOOGLE_APPLICATION_CREDENTIALS: /var/run/secrets/gcp/credentials.json
      OPENSHELL_GATEWAY_ENDPOINT: http://openshell.openshell-system.svc.cluster.local:8080
      OPENSHELL_GATEWAY_NAME: openshell
      SOURCE_REPO: ${{ inputs.source_repo }}
      EVENT_PAYLOAD: ${{ inputs.event_payload }}
      CODE_ALLOWED_TARGET_BRANCHES: ""
      CODE_AUTO_MERGE: "true"
      CODE_AUTO_MERGE_METHOD: squash
      GIT_BOT_EMAIL: fullsend-code@localhost
    steps:
      - name: Checkout workflow repository
        uses: actions/checkout@v4
        with:
          repository: fullsend-dev/.fullsend
          path: .
          fetch-depth: 1

      - name: Checkout target repository
        uses: actions/checkout@v4
        with:
          repository: ${{ inputs.source_repo }}
          path: target-repo
          fetch-depth: 0

      - name: Mint code token
        id: app-token
        uses: ./.github/actions/mint-token
        with:
          role: coder
          repos: ${{ inputs.source_repo }}
          mint_url: http://fullsend-mint-dev.ai-pipeline.svc.cluster.local:8080

      - name: Prepare code context
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
          GITHUB_TOKEN: ${{ steps.app-token.outputs.token }}
        run: |
          set -euo pipefail
          issue_number="$(jq -r '.issue.number // .pull_request.number // empty' <<<"${EVENT_PAYLOAD}")"
          test -n "${issue_number}"
          # Keep the documented GitHub URL shape for upstream script
          # validation; GH_HOST/GITHUB_API_URL route API and git operations to
          # the local emulator.
          issue_url="https://github.com/${SOURCE_REPO}/issues/${issue_number}"
          {
            echo "GITHUB_ISSUE_URL=${issue_url}"
            echo "GITHUB_ISSUE_NUMBER=${issue_number}"
            echo "ISSUE_NUMBER=${issue_number}"
            echo "GH_TOKEN=${GH_TOKEN}"
            echo "GITHUB_TOKEN=${GITHUB_TOKEN}"
            echo "GH_ENTERPRISE_TOKEN=${GH_TOKEN}"
          } >> "${GITHUB_ENV}"

      - name: Run code agent
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
          GITHUB_TOKEN: ${{ steps.app-token.outputs.token }}
          GH_ENTERPRISE_TOKEN: ${{ steps.app-token.outputs.token }}
          PUSH_TOKEN: ${{ steps.app-token.outputs.token }}
          PUSH_TOKEN_SOURCE: github-app
          REPO_FULL_NAME: ${{ inputs.source_repo }}
          MINT_REPOS: triage-target
        run: |
          set -eu
          fullsend run code \
            --fullsend-dir "${GITHUB_WORKSPACE}/.fullsend" \
            --target-repo "${GITHUB_WORKSPACE}/target-repo" \
            --output-dir "${GITHUB_WORKSPACE}/output" \
            --debug=api \
            --forge github
'''


REVIEW_AGENT_WORKFLOW = r'''---
# fullsend-stage: review-agent
# Development implementation of the reusable Fullsend review workflow.
name: Review agent implementation

on:
  workflow_call:
    inputs:
      event_type:
        required: true
        type: string
      source_repo:
        required: true
        type: string
      event_payload:
        required: true
        type: string
    secrets:
      FULLSEND_GCP_WIF_PROVIDER:
        required: false
      FULLSEND_GCP_PROJECT_ID:
        required: false
      OTEL_EXPORTER_OTLP_TRACES_HEADERS:
        required: false

jobs:
  run:
    name: Review agent
    runs-on: [self-hosted, linux, fullsend]
    permissions:
      contents: read
      id-token: write
      issues: write
      pull-requests: write
    env:
      GITHUB_API_URL: https://github.local/api/v3
      GITHUB_SERVER_URL: https://github.local
      GH_HOST: github.local
      FULLSEND_FORGE: github
      FULLSEND_MINT_URL: http://fullsend-mint-dev.ai-pipeline.svc.cluster.local:8080
      NO_SSL_VERIFY: "1"
      CLAUDE_CODE_USE_VERTEX: "1"
      CLOUD_ML_REGION: global
      GOOGLE_APPLICATION_CREDENTIALS: /var/run/secrets/gcp/credentials.json
      OPENSHELL_GATEWAY_ENDPOINT: http://openshell.openshell-system.svc.cluster.local:8080
      OPENSHELL_GATEWAY_NAME: openshell
      SOURCE_REPO: ${{ inputs.source_repo }}
      EVENT_PAYLOAD: ${{ inputs.event_payload }}
      PRIOR_REVIEW_SHA: ""
      PRIOR_REVIEW_PROVENANCE: none
      REVIEW_FINDING_SEVERITY_THRESHOLD: low
      REVIEW_SKIP_AUTHORS: ""
    steps:
      - name: Checkout workflow repository
        uses: actions/checkout@v4
        with:
          repository: fullsend-dev/.fullsend
          path: .
          fetch-depth: 1

      - name: Checkout target repository
        uses: actions/checkout@v4
        with:
          repository: ${{ inputs.source_repo }}
          path: target-repo
          fetch-depth: 1

      - name: Mint review token
        id: app-token
        uses: ./.github/actions/mint-token
        with:
          role: review
          repos: ${{ inputs.source_repo }}
          mint_url: http://fullsend-mint-dev.ai-pipeline.svc.cluster.local:8080

      - name: Prepare review context
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
          GITHUB_TOKEN: ${{ steps.app-token.outputs.token }}
        run: |
          set -euo pipefail
          pr_number="$(jq -r '.pull_request.number // .issue.number // empty' <<<"${EVENT_PAYLOAD}")"
          test -n "${pr_number}"
          # The upstream forge scripts validate GitHub's canonical URL shape;
          # GH_HOST and GITHUB_API_URL below still route all API operations to
          # the local emulator.
          pr_url="https://github.com/${SOURCE_REPO}/pull/${pr_number}"
          {
            echo "GITHUB_PR_URL=${pr_url}"
            echo "GITHUB_ISSUE_URL=${pr_url}"
            echo "PR_NUMBER=${pr_number}"
            echo "GH_TOKEN=${GH_TOKEN}"
            echo "GITHUB_TOKEN=${GITHUB_TOKEN}"
            echo "REVIEW_TOKEN=${GH_TOKEN}"
            echo "GH_ENTERPRISE_TOKEN=${GH_TOKEN}"
          } >> "${GITHUB_ENV}"

      - name: Run review agent
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
          GITHUB_TOKEN: ${{ steps.app-token.outputs.token }}
          GH_ENTERPRISE_TOKEN: ${{ steps.app-token.outputs.token }}
          REVIEW_TOKEN: ${{ steps.app-token.outputs.token }}
          REPO_FULL_NAME: ${{ inputs.source_repo }}
        run: |
          set -eu
          fullsend run review \
            --fullsend-dir "${GITHUB_WORKSPACE}/.fullsend" \
            --target-repo "${GITHUB_WORKSPACE}/target-repo" \
            --output-dir "${GITHUB_WORKSPACE}/output" \
            --debug=api \
            --forge github
'''


FIX_AGENT_WORKFLOW = r'''---
# fullsend-stage: fix-agent
# Development implementation of the reusable Fullsend fix workflow.
name: Fix agent implementation

on:
  workflow_call:
    inputs:
      event_type:
        required: true
        type: string
      source_repo:
        required: true
        type: string
      event_payload:
        required: true
        type: string
    secrets:
      FULLSEND_GCP_WIF_PROVIDER:
        required: false
      FULLSEND_GCP_PROJECT_ID:
        required: false
      OTEL_EXPORTER_OTLP_TRACES_HEADERS:
        required: false

jobs:
  run:
    name: Fix agent
    runs-on: [self-hosted, linux, fullsend]
    permissions:
      contents: write
      id-token: write
      issues: write
      pull-requests: write
    env:
      GITHUB_API_URL: https://github.local/api/v3
      GITHUB_SERVER_URL: https://github.local
      GH_HOST: github.local
      FULLSEND_FORGE: github
      FULLSEND_MINT_URL: http://fullsend-mint-dev.ai-pipeline.svc.cluster.local:8080
      NO_SSL_VERIFY: "1"
      CLAUDE_CODE_USE_VERTEX: "1"
      CLOUD_ML_REGION: global
      GOOGLE_APPLICATION_CREDENTIALS: /var/run/secrets/gcp/credentials.json
      OPENSHELL_GATEWAY_ENDPOINT: http://openshell.openshell-system.svc.cluster.local:8080
      OPENSHELL_GATEWAY_NAME: openshell
      SOURCE_REPO: ${{ inputs.source_repo }}
      EVENT_PAYLOAD: ${{ inputs.event_payload }}
      GIT_BOT_EMAIL: fullsend-fix@localhost
    steps:
      - name: Checkout workflow repository
        uses: actions/checkout@v4
        with:
          repository: fullsend-dev/.fullsend
          path: .
          fetch-depth: 1

      - name: Checkout target repository
        uses: actions/checkout@v4
        with:
          repository: ${{ inputs.source_repo }}
          path: target-repo
          fetch-depth: 0

      - name: Mint fix token
        id: app-token
        uses: ./.github/actions/mint-token
        with:
          role: fix
          repos: ${{ inputs.source_repo }}
          mint_url: http://fullsend-mint-dev.ai-pipeline.svc.cluster.local:8080

      - name: Prepare fix context
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
          GITHUB_TOKEN: ${{ steps.app-token.outputs.token }}
        run: |
          set -euo pipefail
          pr_number="$(jq -r '.pull_request.number // empty' <<<"${EVENT_PAYLOAD}")"
          head_ref="$(jq -r '.pull_request.head.ref // empty' <<<"${EVENT_PAYLOAD}")"
          target_branch="$(jq -r '.pull_request.base.ref // "main"' <<<"${EVENT_PAYLOAD}")"
          trigger_source="$(jq -r '.review.user.login // .comment.user.login // empty' <<<"${EVENT_PAYLOAD}")"
          review_body="$(jq -r '.review.body // empty' <<<"${EVENT_PAYLOAD}")"
          human_instruction="$(jq -r '.comment.body // empty' <<<"${EVENT_PAYLOAD}")"
          [[ "${pr_number}" =~ ^[1-9][0-9]*$ ]]
          [[ "${head_ref}" =~ ^[A-Za-z0-9._/-]+$ ]]
          test -n "${trigger_source}"
          case "${human_instruction}" in
            /fs-fix*) human_instruction="${human_instruction#/fs-fix}"; human_instruction="${human_instruction# }" ;;
            *) human_instruction="" ;;
          esac
          # GitHub exposes pull/<number>/head; the local emulator currently
          # exposes the same-repository branch instead. Keep the production
          # ref first and use the branch only as a local compatibility path.
          if ! git -C target-repo fetch origin "pull/${pr_number}/head:${head_ref}"; then
            git -C target-repo fetch origin "${head_ref}:${head_ref}"
          fi
          git -C target-repo checkout "${head_ref}"
          review_body_file="$(mktemp)"
          printf '%s\n' "${review_body}" > "${review_body_file}"
          pre_agent_head="$(git -C target-repo rev-parse HEAD)"
          pr_url="https://github.com/${SOURCE_REPO}/pull/${pr_number}"
          {
            echo "GITHUB_PR_URL=${pr_url}"
            echo "GITHUB_ISSUE_URL=${pr_url}"
            echo "PR_NUMBER=${pr_number}"
            echo "TARGET_BRANCH=${target_branch}"
            echo "TRIGGER_SOURCE=${trigger_source}"
            echo "FIX_ITERATION=1"
            echo "PRE_AGENT_HEAD=${pre_agent_head}"
            echo "REVIEW_BODY_FILE=${review_body_file}"
            echo "GH_TOKEN=${GH_TOKEN}"
            echo "GITHUB_TOKEN=${GITHUB_TOKEN}"
            echo "GH_ENTERPRISE_TOKEN=${GH_TOKEN}"
            echo "PUSH_TOKEN=${GH_TOKEN}"
            echo "PUSH_TOKEN_SOURCE=github-app"
            echo "REPO_FULL_NAME=${SOURCE_REPO}"
          } >> "${GITHUB_ENV}"
          echo "HUMAN_INSTRUCTION=" >> "${GITHUB_ENV}"
          if [[ -n "${human_instruction}" ]]; then
            {
              echo 'HUMAN_INSTRUCTION<<FULLSEND_HUMAN_INSTRUCTION'
              printf '%s\n' "${human_instruction}"
              echo 'FULLSEND_HUMAN_INSTRUCTION'
            } >> "${GITHUB_ENV}"
          fi

      - name: Run fix agent
        env:
          GH_TOKEN: ${{ steps.app-token.outputs.token }}
          GITHUB_TOKEN: ${{ steps.app-token.outputs.token }}
          GH_ENTERPRISE_TOKEN: ${{ steps.app-token.outputs.token }}
          PUSH_TOKEN: ${{ steps.app-token.outputs.token }}
          PUSH_TOKEN_SOURCE: github-app
          REPO_FULL_NAME: ${{ inputs.source_repo }}
        run: |
          set -eu
          fullsend run fix \
            --fullsend-dir "${GITHUB_WORKSPACE}/.fullsend" \
            --target-repo "${GITHUB_WORKSPACE}/target-repo" \
            --output-dir "${GITHUB_WORKSPACE}/output" \
            --debug=api \
            --forge github
'''


def _force_sonnet5(content: str) -> str:
    """Use Sonnet 5 for every Fullsend agent seeded into this environment."""
    return re.sub(r"(?m)^model:\s*.*$", "model: claude-sonnet-5", content)


def _config_files() -> dict[str, str]:
    source = m9_files()
    files = {
        path: content
        for path, content in source.items()
        if path != ".github/workflows/m9-fullsend-triage.yml"
        and not path.startswith(".fullsend/.github/actions/")
    }
    files[CONFIG_DISPATCH] = DISPATCH_WORKFLOW
    files[CONFIG_TRIAGE] = TRIAGE_WORKFLOW
    files[CONFIG_TRIAGE_AGENT] = TRIAGE_AGENT_WORKFLOW
    files[CONFIG_CODE] = CODE_WORKFLOW
    files[CONFIG_CODE_AGENT] = CODE_AGENT_WORKFLOW
    files[CONFIG_REVIEW] = REVIEW_WORKFLOW
    files[CONFIG_REVIEW_AGENT] = REVIEW_AGENT_WORKFLOW
    files[CONFIG_FIX] = FIX_WORKFLOW
    files[CONFIG_FIX_AGENT] = FIX_AGENT_WORKFLOW
    files[".github/actions/mint-token/action.yml"] = source[APP_ACTION]
    files[".fullsend/config.yaml"] = (
        'version: "1"\nruntime: claude\nroles: [triage, coder, review]\n'
        'agents:\n  - source: agents/triage.yaml\n  - source: agents/code.yaml\n'
        '  - source: agents/review.yaml\n  - source: agents/fix.yaml\n'
    )
    files.update(_code_files())
    files.update(_fix_files())
    # Reuse the pinned review harness and supporting assets from M10, but do
    # not copy its standalone fixture workflow or review-only config file.
    for path, content in m10_review_files().items():
        if path.startswith(".github/workflows/") or path == ".fullsend/config.yaml":
            continue
        files[path] = content
    return {
        path: (
            _force_sonnet5(content)
            if path.startswith(".fullsend/agents/")
            or path.startswith(".fullsend/skills/")
            else content
        )
        for path, content in files.items()
    }


def _code_script(relative: str) -> str:
    """Adapt the pinned GitHub code script for the local GH_HOST."""
    content = _copy(relative)
    return content.replace(
        "https://x-access-token:${token}@github.com/",
        "https://x-access-token:${token}@${GH_HOST:-github.com}/",
    )


def _code_files() -> dict[str, str]:
    """Return the pinned code-agent assets needed for local discovery."""
    harness = _copy("harness/code.yaml").replace(
        "image: ghcr.io/fullsend-ai/fullsend-code@sha256:de3ecbd7719a1927c983142ada96475f3314d2505d0f258bcf19c31411856eb6",
        "image: fullsend-sandbox-dev:k3s",
    )
    harness = harness.replace(
        '        FULLSEND_FORGE: github\n'
        '        GIT_AUTHOR_NAME: "fullsend-code"\n',
        '        FULLSEND_FORGE: github\n'
        '        GH_HOST: "${GH_HOST}"\n'
        '        GITHUB_API_URL: "${GITHUB_API_URL}"\n'
        '        GIT_AUTHOR_NAME: "fullsend-code"\n',
    )
    github_profile = _copy("profiles/fullsend-github-code.yaml")
    github_profile = github_profile.replace("api.github.com", "github.local")
    github_profile = github_profile.replace("github.com", "github.local")
    github_env = _copy("env/github/code.env") + '\nexport GH_HOST="${GH_HOST:-github.local}"\n'
    return {
        ".fullsend/agents/code.yaml": harness,
        ".fullsend/agents/code.md": _copy("agents/code.md"),
        ".fullsend/docs/code.md": _copy("docs/code.md"),
        ".fullsend/scripts/pre-code.sh": _code_script("scripts/pre-code.sh"),
        ".fullsend/scripts/post-code.sh": _code_script("scripts/post-code.sh"),
        ".fullsend/scripts/validate-output-schema.sh": _copy("scripts/validate-output-schema.sh"),
        ".fullsend/schemas/code-result.schema.json": _copy("schemas/code-result.schema.json"),
        ".fullsend/policies/base.yaml": _copy("policies/base.yaml"),
        ".fullsend/profiles/fullsend-github-code.yaml": github_profile,
        ".fullsend/profiles/fullsend-package-registries.yaml": _copy("profiles/fullsend-package-registries.yaml"),
        ".fullsend/profiles/fullsend-gitleaks.yaml": _copy("profiles/fullsend-gitleaks.yaml"),
        ".fullsend/providers/github-code.yaml": _copy("providers/github-code.yaml"),
        ".fullsend/providers/package-registries.yaml": _copy("providers/package-registries.yaml"),
        ".fullsend/providers/gitleaks.yaml": _copy("providers/gitleaks.yaml"),
        ".fullsend/skills/code-implementation/SKILL.md": _copy("skills/code-implementation/SKILL.md"),
        ".fullsend/skills/github-forge/SKILL.md": _copy("skills/github-forge/SKILL.md"),
        ".fullsend/plugins/gopls-lsp/plugin.json": _copy("plugins/gopls-lsp/plugin.json"),
        ".fullsend/env/ssl-cainfo.env": _copy("env/ssl-cainfo.env"),
        ".fullsend/env/github/code.env": github_env,
    }


def _fix_script(relative: str) -> str:
    """Adapt the pinned GitHub fix script for the local GH_HOST."""
    return _copy(relative).replace(
        "https://x-access-token:${token}@github.com/",
        "https://x-access-token:${token}@${GH_HOST:-github.com}/",
    )


def _fix_files() -> dict[str, str]:
    """Return the pinned fix-agent assets needed for local discovery."""
    harness = _copy("harness/fix.yaml").replace(
        "image: ghcr.io/fullsend-ai/fullsend-code@sha256:de3ecbd7719a1927c983142ada96475f3314d2505d0f258bcf19c31411856eb6",
        "image: fullsend-sandbox-dev:k3s",
    )
    harness = harness.replace(
        "        FULLSEND_FORGE: github\n",
        "        FULLSEND_FORGE: github\n        GH_HOST: ${GH_HOST}\n        GITHUB_API_URL: ${GITHUB_API_URL}\n        NO_SSL_VERIFY: \"1\"\n",
        1,
    )
    harness = harness.replace(
        '        GH_TOKEN: "${GH_TOKEN}"\n'
        '        FULLSEND_FORGE: github\n',
        '        GH_TOKEN: "${GH_TOKEN}"\n'
        '        FULLSEND_FORGE: github\n'
        '        GH_HOST: "${GH_HOST}"\n'
        '        GITHUB_API_URL: "${GITHUB_API_URL}"\n'
        '        NO_SSL_VERIFY: "1"\n',
        1,
    )
    github_profile = _copy("profiles/fullsend-github-code.yaml")
    github_profile = github_profile.replace("api.github.com", "github.local")
    github_profile = github_profile.replace("github.com", "github.local")
    github_env = _copy("env/github/fix.env") + '\nexport GH_HOST="${GH_HOST:-github.local}"\n'
    return {
        ".fullsend/agents/fix.yaml": harness,
        ".fullsend/agents/fix.md": _copy("agents/fix.md"),
        ".fullsend/docs/fix.md": _copy("docs/fix.md"),
        ".fullsend/scripts/pre-fix.sh": _fix_script("scripts/pre-fix.sh"),
        ".fullsend/scripts/post-fix.sh": _fix_script("scripts/post-fix.sh"),
        ".fullsend/scripts/validate-output-schema.sh": _copy("scripts/validate-output-schema.sh"),
        ".fullsend/scripts/process-fix-result.py": _copy("scripts/process-fix-result.py"),
        ".fullsend/schemas/fix-result.schema.json": _copy("schemas/fix-result.schema.json"),
        ".fullsend/policies/base.yaml": _copy("policies/base.yaml"),
        ".fullsend/profiles/fullsend-github-code.yaml": github_profile,
        ".fullsend/profiles/fullsend-package-registries.yaml": _copy("profiles/fullsend-package-registries.yaml"),
        ".fullsend/profiles/fullsend-gitleaks.yaml": _copy("profiles/fullsend-gitleaks.yaml"),
        ".fullsend/providers/github-code.yaml": _copy("providers/github-code.yaml"),
        ".fullsend/providers/package-registries.yaml": _copy("providers/package-registries.yaml"),
        ".fullsend/providers/gitleaks.yaml": _copy("providers/gitleaks.yaml"),
        ".fullsend/skills/fix-review/SKILL.md": _copy("skills/fix-review/SKILL.md"),
        ".fullsend/skills/fix-review/github/SKILL.md": _copy("skills/fix-review/github/SKILL.md"),
        ".fullsend/skills/github-forge/SKILL.md": _copy("skills/github-forge/SKILL.md"),
        ".fullsend/skills/code-implementation/SKILL.md": _copy("skills/code-implementation/SKILL.md"),
        ".fullsend/plugins/gopls-lsp/plugin.json": _copy("plugins/gopls-lsp/plugin.json"),
        ".fullsend/env/gcp-vertex.env": _copy("env/gcp-vertex.env"),
        ".fullsend/env/ssl-cainfo.env": _copy("env/ssl-cainfo.env"),
        ".fullsend/env/github/fix.env": github_env,
    }


def _push_files(repo: str, files: dict[str, str], message: str, *, clean_target: bool = False) -> str:
    remote = f"https://x-access-token:{TOKEN}@github.local/{ORG}/{repo}.git"
    with tempfile.TemporaryDirectory(prefix="fullsend-m11-seed-") as temp:
        directory = Path(temp)
        run_git(directory, "init", "--initial-branch=main")
        run_git(directory, "config", "user.name", "Breadboard M11 Seed")
        run_git(directory, "config", "user.email", "breadboard-m11@localhost")
        run_git(directory, "remote", "add", "origin", remote)
        fetched = run_git(directory, "fetch", "origin", "main", check=False)
        if fetched.returncode == 0:
            run_git(directory, "reset", "--hard", "FETCH_HEAD")

        if clean_target:
            for path in (
                directory / ".github/workflows",
                directory / ".github/actions",
                directory / ".fullsend",
            ):
                if path.exists():
                    shutil.rmtree(path)

        for relative, content in files.items():
            path = directory / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")

        if clean_target:
            # The directories may no longer exist after cleanup.  Stage all
            # tracked deletions/edits, but add new files only from ``files``
            # so unrelated untracked target data is never swept into a seed
            # commit.
            run_git(directory, "add", "-u")
            run_git(directory, "add", "--", *files)
        else:
            run_git(directory, "add", "--", *files)
        staged = run_git(directory, "diff", "--cached", "--quiet", check=False)
        if staged.returncode != 0:
            run_git(directory, "commit", "-m", message)
            pushed = run_git(directory, "push", "-u", "origin", "main", check=False)
            if pushed.returncode != 0:
                raise RuntimeError(f"git push failed for {repo}: {pushed.stderr or pushed.stdout}")
        return run_git(directory, "rev-parse", "HEAD").stdout.strip()


def _ensure_config_repo() -> None:
    status, _ = api_request("GET", f"/repos/{ORG}/{CONFIG_REPO}")
    if status == 200:
        return
    if status != 404:
        raise RuntimeError(f"GET config repository failed: HTTP {status}")
    status, payload = api_request(
        "POST", f"/orgs/{ORG}/repos",
        {"name": CONFIG_REPO, "description": "Fullsend development configuration", "private": False},
    )
    if status not in (201, 422):
        raise RuntimeError(f"POST config repository failed: HTTP {status}: {payload}")


def _ensure_bot_push_access(repo: str, bot_login: str) -> None:
    """Give a mutating Fullsend bot collaborator permission for Git pushes."""
    status, payload = api_request(
        "PUT",
        f"/repos/{ORG}/{repo}/collaborators/{quote(bot_login, safe='')}",
        {"permission": "push"},
    )
    if status != 201:
        raise RuntimeError(
            f"Could not grant {bot_login} push access to {ORG}/{repo}: "
            f"HTTP {status}: {payload}"
        )


def _workflows(repo: str) -> list[dict]:
    status, payload = api_request("GET", f"/repos/{ORG}/{repo}/actions/workflows")
    if status != 200 or not isinstance(payload, dict):
        raise RuntimeError(f"GET workflows failed for {repo}: HTTP {status}: {payload}")
    return payload.get("workflows", [])


def main() -> int:
    ensure_org()
    ensure_repo()
    _ensure_bot_push_access(REPO, "fullsend-code[bot]")
    _ensure_bot_push_access(REPO, "fullsend-fix[bot]")
    _ensure_config_repo()

    config_commit = _push_files(
        CONFIG_REPO,
        _config_files(),
        "Add centralized Fullsend stage routing and agent callers",
    )
    target_commit = _push_files(
        REPO,
        {TARGET_WORKFLOW: SHIM_WORKFLOW},
        "Replace fixture workflows with the Fullsend event shim",
        clean_target=True,
    )
    target_workflows = _workflows(REPO)
    config_workflows = _workflows(CONFIG_REPO)
    target_paths = sorted({
        item.get("path") for item in target_workflows
        if item.get("state") == "active"
    })
    config_paths = sorted({
        item.get("path") for item in config_workflows
        if item.get("state") == "active"
    })
    if target_paths != [TARGET_WORKFLOW]:
        raise RuntimeError(f"target active workflow cleanup incomplete: {target_paths}")
    expected_config = sorted(
        (
            CONFIG_DISPATCH,
            CONFIG_TRIAGE,
            CONFIG_TRIAGE_AGENT,
            CONFIG_CODE,
            CONFIG_CODE_AGENT,
            CONFIG_REVIEW,
            CONFIG_REVIEW_AGENT,
            CONFIG_FIX,
            CONFIG_FIX_AGENT,
        )
    )
    if config_paths != expected_config:
        raise RuntimeError(f"config workflow setup incomplete: {config_paths}")
    print(json.dumps({
        "status": "seeded",
        "target_repository": f"{ORG}/{REPO}",
        "config_repository": f"{ORG}/{CONFIG_REPO}",
        "target_commit": target_commit,
        "config_commit": config_commit,
        "target_workflows": target_paths,
        "config_workflows": config_paths,
        "automatic_agent_dispatch": {
            "triage": "issues:opened|edited, ready-for-triage, human comments on needs-info issues, /fs-triage",
            "code": "ready-to-code, /fs-code",
            "review": "ready-for-review, /fs-review, pull request review events",
            "fix": "CHANGES_REQUESTED reviews, /fs-fix",
        },
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as exc:
        print(f"M11 seed failed: {exc}", file=sys.stderr)
        raise SystemExit(1)
