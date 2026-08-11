#!/usr/bin/env bash
set -euo pipefail

STAGE="${1:-all}"
SHA_TAG="${GITHUB_SHA:-local}"

run_python() {
  python -m pip install --upgrade pip
  python -m pip install -e ".[security]"
  python -m ruff check services ai_platform tests scripts
  python -m pytest
  python -m bandit -r services ai_platform scripts -x "services/user-service/tests,services/product-service/tests,services/order-service/tests,tests"
}

run_docker() {
  docker build -t "ai-user-service:${SHA_TAG}" -t ai-user-service:local services/user-service
  docker build -t "ai-product-service:${SHA_TAG}" -t ai-product-service:local services/product-service
  docker build -t "ai-order-service:${SHA_TAG}" -t ai-order-service:local services/order-service

  trivy image --format table --severity CRITICAL,HIGH --exit-code 1 --ignore-unfixed "ai-user-service:${SHA_TAG}"
  trivy image --format table --severity CRITICAL,HIGH --exit-code 1 --ignore-unfixed "ai-product-service:${SHA_TAG}"
  trivy image --format table --severity CRITICAL,HIGH --exit-code 1 --ignore-unfixed "ai-order-service:${SHA_TAG}"
}

run_kubernetes() {
  python -m pip install PyYAML
  python scripts/validate-kubernetes-manifests.py

  kubectl config use-context docker-desktop
  kubectl apply -f kubernetes/user-service
  kubectl apply -f kubernetes/product-service
  kubectl apply -f kubernetes/order-service
}

case "${STAGE}" in
  python)
    run_python
    ;;
  docker)
    run_docker
    ;;
  kubernetes)
    run_kubernetes
    ;;
  all)
    run_python
    run_docker
    run_kubernetes
    ;;
  *)
    echo "Unknown CI stage: ${STAGE}" >&2
    exit 2
    ;;
esac
