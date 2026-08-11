#!/usr/bin/env bash
set -euo pipefail

REGISTRY_HOST="${LOCAL_REGISTRY_HOST:-localhost:5001}"
REGISTRY_NAME="${LOCAL_REGISTRY_NAME:-ai-platform-registry}"

if ! docker ps --format '{{.Names}}' | grep -qx "${REGISTRY_NAME}"; then
  if docker ps -a --format '{{.Names}}' | grep -qx "${REGISTRY_NAME}"; then
    docker start "${REGISTRY_NAME}"
  else
    docker run -d -p 5001:5000 --restart=always --name "${REGISTRY_NAME}" registry:2
  fi
fi

docker build -t ai-user-service:local -t "${REGISTRY_HOST}/ai-user-service:local" services/user-service
docker build -t ai-product-service:local -t "${REGISTRY_HOST}/ai-product-service:local" services/product-service
docker build -t ai-order-service:local -t "${REGISTRY_HOST}/ai-order-service:local" services/order-service

docker push "${REGISTRY_HOST}/ai-user-service:local"
docker push "${REGISTRY_HOST}/ai-product-service:local"
docker push "${REGISTRY_HOST}/ai-order-service:local"

kubectl apply -f kubernetes/user-service
kubectl apply -f kubernetes/product-service
kubectl apply -f kubernetes/order-service

kubectl rollout restart deployment/user-service deployment/product-service deployment/order-service
kubectl rollout status deployment/user-service --timeout=120s
kubectl rollout status deployment/product-service --timeout=120s
kubectl rollout status deployment/order-service --timeout=120s
