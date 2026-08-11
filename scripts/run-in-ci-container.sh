#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${CI_TOOLBOX_IMAGE:-ai-platform-ci-tools:local}"
COMMAND="${1:-all}"

docker build -t "${IMAGE_NAME}" -f docker/ci/Dockerfile .

DOCKER_ARGS=(
  --rm
  -v "${PWD}:/workspace"
  -w /workspace
  -v /var/run/docker.sock:/var/run/docker.sock
  -e GITHUB_TOKEN="${GITHUB_TOKEN:-}"
  -e GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-}"
  -e GITHUB_RUN_ID="${GITHUB_RUN_ID:-}"
  -e GITHUB_SHA="${GITHUB_SHA:-local}"
  -e GITHUB_REF_NAME="${GITHUB_REF_NAME:-}"
  -e FAILED_RUN_ID="${FAILED_RUN_ID:-}"
  -e FAILED_HEAD_SHA="${FAILED_HEAD_SHA:-}"
  -e FAILED_HEAD_BRANCH="${FAILED_HEAD_BRANCH:-}"
)

if [[ -d /Users/admin/.kube ]]; then
  DOCKER_ARGS+=(-v /Users/admin/.kube:/root/.kube:ro)
elif [[ -d "${HOME}/.kube" ]]; then
  DOCKER_ARGS+=(-v "${HOME}/.kube:/root/.kube:ro)
fi

case "${COMMAND}" in
  python|docker|kubernetes|all)
    docker run "${DOCKER_ARGS[@]}" "${IMAGE_NAME}" bash -lc "scripts/ci_pipeline.sh ${COMMAND}"
    ;;
  ai-remediation)
    docker run "${DOCKER_ARGS[@]}" "${IMAGE_NAME}" bash -lc "python scripts/ai_remediation_job.py"
    ;;
  *)
    echo "Unknown command: ${COMMAND}" >&2
    exit 2
    ;;
esac
