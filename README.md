
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

## Phase 2 Status: ✅ COMPLETE
- [x] Chaos scripts (pod killer, network delay)
- [x] Recovery time tracking (9-13 seconds average)
- [x] Service availability testing during failures
- [x] Documented chaos test results

## Phase 3 Status: ✅ COMPLETE
- [x] Prometheus metrics collection
- [x] Custom application metrics (request rate, latency, errors)
- [x] Grafana dashboard with real-time visualization
- [x] Chaos impact visible in metrics (latency spikes, error rates)

## Phase 4 Status: ✅ COMPLETE
- [x] Jenkins CI/CD pipeline (host-based)
- [x] Automated Docker image builds
- [x] Automated KIND cluster deployments
- [x] Integrated chaos testing in pipeline
- [x] Automated recovery validation (<30s threshold)
- [x] Full end-to-end automation

## CI/CD Pipeline Features
- **Build**: Multi-service Docker image builds
- **Deploy**: Automated Kubernetes deployments via kubectl
- **Test**: Chaos engineering with automated pod failure injection
- **Validate**: Recovery time measurement with pass/fail gates
- **Report**: Console output with detailed metrics

## Running the Pipeline
```bash
# Access Jenkins
http://localhost:8080

# Trigger build
Click "Build Now" on chaos-resilient-pipeline

# View results
Check Console Output for build logs and chaos test results
```

## Project Architecture
```
Developer commits → GitHub
                      ↓
                   Jenkins detects change
                      ↓
              Builds Docker images locally
                      ↓
              Loads images to KIND cluster
                      ↓
         Deploys to Kubernetes (kubectl)
                      ↓
            Runs automated chaos tests
                      ↓
         Validates recovery time (<30s)
                      ↓
                   ✅ SUCCESS
```