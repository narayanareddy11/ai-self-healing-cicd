#!/usr/bin/env bash
set -euo pipefail

docker build -t ai-user-service:local services/user-service
docker build -t ai-product-service:local services/product-service
docker build -t ai-order-service:local services/order-service

kubectl apply -f kubernetes/user-service
kubectl apply -f kubernetes/product-service
kubectl apply -f kubernetes/order-service

kubectl rollout status deployment/user-service
kubectl rollout status deployment/product-service
kubectl rollout status deployment/order-service
