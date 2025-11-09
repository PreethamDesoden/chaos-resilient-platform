#!/bin/bash

echo "�� Starting Chaos-Resilient Platform..."
echo ""

# Check Docker
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker not running. Start Docker Desktop first!"
    exit 1
fi

# Check if cluster exists
if ! kind get clusters 2>/dev/null | grep -q "chaos-platform"; then
    echo "📦 Creating KIND cluster..."
    kind create cluster --name chaos-platform
    
    echo "🔨 Building Docker images..."
    docker build -q -t order-service:v1 ./services/order-service
    docker build -q -t inventory-service:v1 ./services/inventory-service
    docker build -q -t notification-service:v1 ./services/notification-service
    
    echo "📤 Loading images to cluster..."
    kind load docker-image order-service:v1 --name chaos-platform
    kind load docker-image inventory-service:v1 --name chaos-platform
    kind load docker-image notification-service:v1 --name chaos-platform
    
    echo "🎯 Deploying services..."
    kubectl apply -f kubernetes/manifests/ > /dev/null
    
    echo "📊 Installing monitoring stack..."
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts > /dev/null 2>&1
    helm repo update > /dev/null 2>&1
    kubectl create namespace monitoring > /dev/null 2>&1
    helm install prometheus prometheus-community/kube-prometheus-stack \
      --namespace monitoring \
      --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false > /dev/null 2>&1
    
    kubectl apply -f monitoring/order-service-monitor.yaml > /dev/null 2>&1
    
    echo "⏳ Waiting for pods (60s)..."
    sleep 60
else
    echo "✅ Cluster exists, starting containers..."
    docker start chaos-platform-control-plane > /dev/null 2>&1
    sleep 10
fi

# Update Jenkins kubeconfig
echo "🔧 Configuring Jenkins..."
kind export kubeconfig --name chaos-platform > /dev/null 2>&1
sudo mkdir -p /var/lib/jenkins/.kube > /dev/null 2>&1
sudo cp ~/.kube/config /var/lib/jenkins/.kube/config > /dev/null 2>&1
sudo chown -R jenkins:jenkins /var/lib/jenkins/.kube > /dev/null 2>&1

# Start Jenkins
echo "⚙️  Starting Jenkins..."
sudo systemctl start jenkins > /dev/null 2>&1

# Port forwards
echo "🔗 Setting up port-forwards..."
pkill -f "port-forward" > /dev/null 2>&1
kubectl port-forward -n jenkins svc/jenkins 8080:8080 > /dev/null 2>&1 &
kubectl port-forward svc/order-service 5000:5000 > /dev/null 2>&1 &
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80 > /dev/null 2>&1 &
sleep 3

# Get status
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ PLATFORM READY!"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🌐 URLs:"
echo "   Jenkins:  http://localhost:8080"
echo "   Grafana:  http://localhost:3000"
echo "   API:      http://localhost:5000"
echo ""
echo "🔑 Grafana Password:"
kubectl get secret --namespace monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" 2>/dev/null | base64 -d
echo ""
echo ""
echo "📊 Pod Status:"
kubectl get pods --all-namespaces | grep -E "order-service|inventory|notification|grafana" | grep -v "Completed"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "To stop: ./stop.sh"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
