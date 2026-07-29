#!/usr/bin/env bash
# Run a validation probe recipe through Harbor with CAPI (Copilot gateway) as the
# persona model. Wraps all the env wiring that host-native survey / CAPI need.
#
# Usage:
#   application/validation/scripts/run_probe.sh <recipe.yaml> [survey_task_path]
#
# Examples:
#   application/validation/scripts/run_probe.sh application/validation/recipes/survey-pos.yaml \
#       application/validation/tasks/probe-survey_code-comment
#
# Requires: a Copilot gho_ token in one of the known .env files (see below), uv, docker.
set -euo pipefail

RECIPE="${1:?usage: run_probe.sh <recipe.yaml> [survey_task_path]}"
SURVEY_TASK_PATH="${2:-}"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../../.." && pwd)"
cd "$REPO_ROOT"

# --- CAPI token: prefer already-exported, else read from known .env files ---
if [ -z "${CAPI_API_KEY:-}" ]; then
  for envf in \
    /mnt/nvme/jintao/project/fastedit/fastedit/.env \
    /mnt/nvme/jintao/project/adk-measurement/.env; do
    if [ -f "$envf" ]; then
      tok=$(grep -E '^GITHUB_COPILOT_TOKEN=' "$envf" 2>/dev/null | sed -E "s/^[^=]*=//; s/['\"]//g" | tr -d ' ' | head -1)
      if [ -n "$tok" ]; then CAPI_API_KEY="$tok"; break; fi
    fi
  done
fi
: "${CAPI_API_KEY:?no Copilot token found; export CAPI_API_KEY=gho_... or add it to a known .env}"
export CAPI_API_KEY
export CAPI_BASE_URL="${CAPI_BASE_URL:-https://api.githubcopilot.com}"

# --- PYTHONPATH so host-native persona agents can import `backend` etc. ---
export PYTHONPATH="${REPO_ROOT}:${REPO_ROOT}/environment/runtime:${REPO_ROOT}/packages/playground/src:${REPO_ROOT}/application/playground${PYTHONPATH:+:${PYTHONPATH}}"

# --- host-native survey agent needs the task path explicitly ---
if [ -n "$SURVEY_TASK_PATH" ]; then
  export MATRIX_SURVEY_TASK_PATH="${REPO_ROOT}/${SURVEY_TASK_PATH#"${REPO_ROOT}/"}"
fi

echo "[run_probe] recipe=$RECIPE"
echo "[run_probe] CAPI_BASE_URL=$CAPI_BASE_URL  token_len=${#CAPI_API_KEY}"
[ -n "${MATRIX_SURVEY_TASK_PATH:-}" ] && echo "[run_probe] MATRIX_SURVEY_TASK_PATH=$MATRIX_SURVEY_TASK_PATH"

exec uv run harbor run -c "$RECIPE"
