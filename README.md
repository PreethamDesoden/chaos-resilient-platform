
# Chaos-Resilient Microservices Platform

Self-healing microservices platform with automated chaos engineering and observability.

## Architecture
- **Order Service**: Handles order creation and orchestration
- **Inventory Service**: Manages product inventory and stock
- **Notification Service**: Sends order confirmations

## Tech Stack
- Docker (containerization)
- Kubernetes/KIND (orchestration)
- Python/Flask (microservices)
- Jenkins (CI/CD) - Phase 2
- Prometheus/Grafana (monitoring) - Phase 3
- Terraform (IaC) - Phase 4
- Ansible (configuration) - Phase 4

## Phase 1 Status: ✅ COMPLETE
- [x] 3 microservices built
- [x] Docker images created
- [x] Kubernetes deployments configured
- [x] Health/readiness probes implemented
- [x] Inter-service communication working
- [x] End-to-end order flow tested

## Quick Start
```bash
# Build images
docker build -t order-service:v1 ./services/order-service
docker build -t inventory-service:v1 ./services/inventory-service
docker build -t notification-service:v1 ./services/notification-service

# Create KIND cluster
kind create cluster --name chaos-platform

# Load images
kind load docker-image order-service:v1 --name chaos-platform
kind load docker-image inventory-service:v1 --name chaos-platform
kind load docker-image notification-service:v1 --name chaos-platform

# Deploy
kubectl apply -f kubernetes/manifests/

# Test
kubectl port-forward svc/order-service 5000:5000 &
curl -X POST http://localhost:5000/orders -H "Content-Type: application/json" -d '{"product_id":"PROD-001","quantity":2,"email":"test@example.com"}'
```

## Next: Phase 2 - Chaos Engineering
