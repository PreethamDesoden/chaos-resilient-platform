# System Architecture

## High-Level Overview
```
┌─────────────────────────────────────────────────────────────────────┐
│                         Developer Workflow                           │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ git push
                                   ▼
                         ┌─────────────────┐
                         │     GitHub      │
                         │   Repository    │
                         └────────┬────────┘
                                  │
                                  │ webhook/poll
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                           CI/CD Pipeline                             │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                      Jenkins                               │    │
│  │                                                             │    │
│  │  1. Checkout Code                                          │    │
│  │  2. Build Docker Images (order, inventory, notification)   │    │
│  │  3. Load Images to KIND Cluster                            │    │
│  │  4. Deploy via kubectl                                     │    │
│  │  5. Run Chaos Tests (pod-killer.sh)                        │    │
│  │  6. Validate Recovery Time (<30s)                          │    │
│  │  7. ✅ Pass or ❌ Fail                                      │    │
│  └────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────┘
                                   │
                                   │ kubectl apply
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Kubernetes Cluster (KIND)                         │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                    Default Namespace                         │   │
│  │                                                               │   │
│  │  ┌──────────────────┐      ┌──────────────────┐            │   │
│  │  │  Order Service   │◄────►│ Inventory Service│            │   │
│  │  │   (2 replicas)   │      │   (2 replicas)   │            │   │
│  │  └────────┬─────────┘      └──────────────────┘            │   │
│  │           │                                                  │   │
│  │           │                                                  │   │
│  │           ▼                                                  │   │
│  │  ┌──────────────────┐                                       │   │
│  │  │Notification Svc  │                                       │   │
│  │  │   (2 replicas)   │                                       │   │
│  │  └──────────────────┘                                       │   │
│  │                                                               │   │
│  │  Each pod has:                                               │   │
│  │  • Liveness Probe  (restart if unhealthy)                   │   │
│  │  • Readiness Probe (traffic only when ready)                │   │
│  │  • Resource Limits (prevent resource hogging)               │   │
│  │  • /metrics endpoint (Prometheus scraping)                  │   │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │                  Monitoring Namespace                        │   │
│  │                                                               │   │
│  │  ┌──────────────┐        ┌──────────────┐                  │   │
│  │  │  Prometheus  │───────►│   Grafana    │                  │   │
│  │  │              │        │              │                  │   │
│  │  │ • Scrapes    │        │ • Dashboards │                  │   │
│  │  │   /metrics   │        │ • Alerts     │                  │   │
│  │  │ • Stores     │        │ • Visual.    │                  │   │
│  │  │   time-series│        │              │                  │   │
│  │  └──────────────┘        └──────────────┘                  │   │
│  │         ▲                                                    │   │
│  │         │                                                    │   │
│  │         │ scrapes every 15s                                 │   │
│  │         │                                                    │   │
│  │  ┌──────┴────────────────────────────────────────┐         │   │
│  │  │        ServiceMonitor (CRD)                    │         │   │
│  │  │  Tells Prometheus where to scrape metrics     │         │   │
│  │  └────────────────────────────────────────────────┘         │   │
│  └───────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────┘
                                   ▲
                                   │
                                   │ chaos injection
                                   │
                         ┌─────────┴────────┐
                         │  Chaos Scripts   │
                         │                  │
                         │ • pod-killer.sh  │
                         │ • Random pod kill│
                         │ • Measure MTTR   │
                         └──────────────────┘
```

## Request Flow (Normal Operation)
```
User Request
     │
     ▼
┌─────────────────┐
│ kubectl port-   │
│ forward :5000   │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────┐
│      Kubernetes Service                 │
│      (Load Balancer)                    │
│                                          │
│  Routes to healthy pods only            │
│  (based on readiness probe)             │
└────────┬────────────────────────────────┘
         │
         ├─────────────┬─────────────┐
         ▼             ▼             ▼
   ┌─────────┐   ┌─────────┐   ┌─────────┐
   │ Pod 1   │   │ Pod 2   │   │ Pod N   │
   │ Ready   │   │ Ready   │   │ Ready   │
   └────┬────┘   └────┬────┘   └────┬────┘
        │             │             │
        ▼             ▼             ▼
   Order Service checks inventory
        │
        ▼
   Inventory Service responds
        │
        ▼
   Order Service sends notification
        │
        ▼
   Notification Service confirms
        │
        ▼
   Response to User
```

## Chaos Scenario Flow
```
Time: T+0s
┌─────────────────────────────────┐
│   All 3 services healthy         │
│   • order-service: 2/2 running  │
│   • inventory: 2/2 running      │
│   • notification: 2/2 running   │
└─────────────────────────────────┘
              │
              │ pod-killer.sh executes
              ▼
Time: T+1s
┌─────────────────────────────────┐
│ 🔥 Random pod killed             │
│   kubectl delete pod --force    │
└─────────────────────────────────┘
              │
              ▼
Time: T+2s
┌─────────────────────────────────┐
│ Kubernetes detects:              │
│   Actual pods: 1                │
│   Desired replicas: 2           │
│   Status: DEGRADED              │
└─────────────────────────────────┘
              │
              ▼
Time: T+3s
┌─────────────────────────────────┐
│ Scheduler starts new pod         │
│   • Pulls image from cache      │
│   • Mounts volumes              │
│   • Starts container            │
└─────────────────────────────────┘
              │
              ▼
Time: T+5s
┌─────────────────────────────────┐
│ Health checks begin:             │
│   Liveness:  ❌ (not ready yet) │
│   Readiness: ❌ (dependencies)  │
└─────────────────────────────────┘
              │
              ▼
Time: T+10s
┌─────────────────────────────────┐
│ Health checks pass:              │
│   Liveness:  ✅                 │
│   Readiness: ✅                 │
│   Traffic:   Enabled            │
└─────────────────────────────────┘
              │
              ▼
Time: T+13s
┌─────────────────────────────────┐
│ ✅ RECOVERY COMPLETE             │
│   All 3 services: 2/2 running   │
│   MTTR: 13 seconds              │
│   Pipeline: PASS                │
└─────────────────────────────────┘
```

## Metrics Collection Flow
```
┌─────────────────────────────────────────────────────────┐
│                  Application Code                        │
│                                                           │
│  from metrics import track_order_request                │
│                                                           │
│  @app.route('/orders', methods=['POST'])                │
│  def create_order():                                     │
│      start_time = time.time()                           │
│      ...                                                 │
│      track_order_request('success', product_id)         │
│      track_request_duration('/orders', duration)        │
│                                                           │
└───────────────────────┬─────────────────────────────────┘
                        │
                        │ exposes /metrics endpoint
                        ▼
┌─────────────────────────────────────────────────────────┐
│              Prometheus Client Library                   │
│                                                           │
│  order_requests_total{status="success",product="X"}: 42 │
│  order_request_duration_seconds{quantile="0.95"}: 0.23 │
│  inventory_requests_total{status="success"}: 40         │
│                                                           │
└───────────────────────┬─────────────────────────────────┘
                        │
                        │ HTTP GET /metrics (every 15s)
                        ▼
┌─────────────────────────────────────────────────────────┐
│                   Prometheus Server                      │
│                                                           │
│  • Scrapes all /metrics endpoints                       │
│  • Stores time-series data                              │
│  • Evaluates alerting rules                             │
│  • Provides PromQL query API                            │
│                                                           │
└───────────────────────┬─────────────────────────────────┘
                        │
                        │ PromQL queries
                        ▼
┌─────────────────────────────────────────────────────────┐
│                      Grafana                             │
│                                                           │
│  Dashboard Panels:                                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │ rate(order_requests_total[1m])                  │   │
│  │ ▁▂▃▅▇█▇▅▃▂▁  (real-time chart)                 │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
│  ┌─────────────────────────────────────────────────┐   │
│  │ histogram_quantile(0.95, ...)                   │   │
│  │ Latency: 230ms                                  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                           │
└─────────────────────────────────────────────────────────┘
```

## Technology Stack Layers
```
┌──────────────────────────────────────────────────────┐
│               Application Layer                       │
│  • Python 3.11 + Flask                               │
│  • Gunicorn (production WSGI server)                 │
│  • Custom business logic                             │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────┴─────────────────────────────────────┐
│             Containerization Layer                    │
│  • Docker (multi-stage builds)                       │
│  • Image optimization (<200MB)                       │
│  • Health check endpoints built-in                   │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────┴─────────────────────────────────────┐
│            Orchestration Layer                        │
│  • Kubernetes (KIND for local)                       │
│  • Deployments (replica management)                  │
│  • Services (load balancing)                         │
│  • Probes (self-healing)                             │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────┴─────────────────────────────────────┐
│            Observability Layer                        │
│  • Prometheus (metrics collection)                   │
│  • Grafana (visualization)                           │
│  • Custom exporters                                  │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────┴─────────────────────────────────────┐
│               CI/CD Layer                             │
│  • Jenkins (pipeline orchestration)                  │
│  • Git (version control)                             │
│  • Automated testing                                 │
└────────────────┬─────────────────────────────────────┘
                 │
┌────────────────┴─────────────────────────────────────┐
│          Chaos Engineering Layer                      │
│  • Automated failure injection                       │
│  • Recovery time measurement                         │
│  • SLA validation                                    │
└──────────────────────────────────────────────────────┘
```

## Key Design Patterns

### 1. Circuit Breaker Pattern
```
Request → Order Service
            │
            ├─→ Try: Call Inventory
            │    ├─ Success → Continue
            │    └─ Timeout (3s) → Return 503
            │
            └─→ Don't hang forever
```

### 2. Retry with Exponential Backoff
```
Attempt 1: Immediate
    ↓ fail
Attempt 2: Wait 1s
    ↓ fail
Attempt 3: Wait 2s
    ↓ fail
Give up → Return error
```

### 3. Graceful Degradation
```
Order Flow:
  1. Check Inventory → ✅ Success
  2. Create Order     → ✅ Success
  3. Send Email       → ❌ Failed
     └─→ Log warning, DON'T fail order
     
Result: Order confirmed, email delayed
```

### 4. Health Check Strategy
```
Liveness Probe (am I alive?):
  GET /health → 200 OK
  └─ If fails 3x → Kill pod

Readiness Probe (can I serve traffic?):
  GET /ready → Check dependencies
  └─ If fails 2x → Remove from service
```

## Deployment Strategy
```
Rolling Update (Zero Downtime):

Before:
  Pod-old-1 ✅ ─┐
  Pod-old-2 ✅ ─┤ → Traffic
  
Step 1: Create new pod
  Pod-old-1 ✅ ─┐
  Pod-old-2 ✅ ─┤ → Traffic
  Pod-new-1 🔄 (starting)

Step 2: New pod ready
  Pod-old-1 ✅ ─┐
  Pod-old-2 ✅ ─┤ → Traffic
  Pod-new-1 ✅ ─┘

Step 3: Terminate old pod
  Pod-old-2 ✅ ─┐ → Traffic
  Pod-new-1 ✅ ─┘
  Pod-old-1 ❌ (terminating)

Step 4: Create second new pod
  Pod-old-2 ✅ ─┐
  Pod-new-1 ✅ ─┤ → Traffic
  Pod-new-2 🔄 (starting)

Final:
  Pod-new-1 ✅ ─┐
  Pod-new-2 ✅ ─┘ → Traffic
  
Total downtime: 0 seconds
```

---

**Legend:**
- ✅ Healthy/Running
- ❌ Failed/Terminated
- 🔄 Starting/Processing
- ▲ Increase
- ▼ Decrease
- ◄─► Bidirectional communication
- ─→ Unidirectional flow