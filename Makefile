.PHONY: help lint test security docker-build k8s-validate k8s-apply

help:
	@echo "AI-Assisted Self-Healing CI/CD Platform"
	@echo ""
	@echo "Targets:"
	@echo "  lint          Run Ruff"
	@echo "  test          Run pytest"
	@echo "  security      Run Bandit when installed"
	@echo "  docker-build  Build all service images"
	@echo "  k8s-validate  Validate Kubernetes manifests with kubectl dry-run"
	@echo "  k8s-apply     Apply Kubernetes manifests"

lint:
	python3 -m ruff check services ai_platform tests

test:
	python3 -m pytest

security:
	python3 -m bandit -r services ai_platform -x "services/user-service/tests,services/product-service/tests,services/order-service/tests"

docker-build:
	docker build -t ai-user-service:local services/user-service
	docker build -t ai-product-service:local services/product-service
	docker build -t ai-order-service:local services/order-service

k8s-validate:
	kubectl apply --dry-run=client -f kubernetes/user-service
	kubectl apply --dry-run=client -f kubernetes/product-service
	kubectl apply --dry-run=client -f kubernetes/order-service

k8s-apply:
	kubectl apply -f kubernetes/user-service
	kubectl apply -f kubernetes/product-service
	kubectl apply -f kubernetes/order-service
