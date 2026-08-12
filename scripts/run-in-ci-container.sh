#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME="${CI_TOOLBOX_IMAGE:-ai-platform-ci-tools:local}"
COMMAND="${1:-all}"
TRIVY_CACHE_DIR="${TRIVY_CACHE_DIR:-/tmp/ai-platform-trivy-cache}"

docker build -t "${IMAGE_NAME}" -f docker/ci/Dockerfile .
mkdir -p "${TRIVY_CACHE_DIR}"
chmod 0777 "${TRIVY_CACHE_DIR}"

DOCKER_ARGS=(
  --rm
  -v "${PWD}:/workspace"
  -w /workspace
  -v /var/run/docker.sock:/var/run/docker.sock
  -v "${TRIVY_CACHE_DIR}:/root/.cache/trivy"
  -e GITHUB_TOKEN="${GITHUB_TOKEN:-}"
  -e GITHUB_REPOSITORY="${GITHUB_REPOSITORY:-}"
  -e GITHUB_RUN_ID="${GITHUB_RUN_ID:-}"
  -e GITHUB_SHA="${GITHUB_SHA:-local}"
  -e GITHUB_REF_NAME="${GITHUB_REF_NAME:-}"
  -e FAILED_RUN_ID="${FAILED_RUN_ID:-}"
  -e FAILED_HEAD_SHA="${FAILED_HEAD_SHA:-}"
  -e FAILED_HEAD_BRANCH="${FAILED_HEAD_BRANCH:-}"
  -e LLM_PROVIDER="${LLM_PROVIDER:-ollama}"
  -e LLM_MODEL="${LLM_MODEL:-qwen2.5:3b}"
  -e OLLAMA_BASE_URL="${OLLAMA_BASE_URL:-http://host.docker.internal:11434}"
  -e PYTHONPATH=/workspace
  -e RUFF_CACHE_DIR=/tmp/ruff-cache
)

if [[ -d /Users/admin/.kube ]]; then
  DOCKER_ARGS+=(-v /Users/admin/.kube:/host-kube:ro -e KUBECONFIG=/tmp/kube/config)
elif [[ -d "${HOME}/.kube" ]]; then
  DOCKER_ARGS+=(-v "${HOME}/.kube:/host-kube:ro" -e KUBECONFIG=/tmp/kube/config)
fi

case "${COMMAND}" in
  python|docker|kubernetes|all)
    docker run "${DOCKER_ARGS[@]}" "${IMAGE_NAME}" bash -lc "scripts/ci_pipeline.sh ${COMMAND}"
    ;;
  ai-remediation)
    docker run \
      "${DOCKER_ARGS[@]}" \
      --user "$(id -u):$(id -g)" \
      -e HOME=/tmp \
      "${IMAGE_NAME}" bash -lc '
      python -m pip install --user \
        "fastapi>=0.115.0" \
        "httpx>=0.27.0" \
        "langgraph>=1.2.9,<2.0.0" \
        "pydantic>=2.8.0" \
        "pytest>=8.3.0" \
        "PyYAML>=6.0.0" \
        "ruff>=0.6.0" \
        "uvicorn[standard]>=0.30.0" \
        "bandit>=1.7.9" \
      && python scripts/ai_remediation_job.py
    '
    ;;
  *)
    echo "Unknown command: ${COMMAND}" >&2
    exit 2
    ;;
esac
