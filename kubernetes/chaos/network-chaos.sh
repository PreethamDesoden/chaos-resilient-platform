#!/bin/bash

RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

echo -e "${YELLOW}=== Network Chaos: Adding Latency ===${NC}\n"

# Get a random order-service pod
POD=$(kubectl get pods -l app=order-service -o jsonpath='{.items[0].metadata.name}')

echo -e "${YELLOW}Target pod: ${POD}${NC}"
echo -e "${RED}Adding 2 second network delay...${NC}\n"

# Execute inside pod to add network delay
kubectl exec ${POD} -- sh -c "apt-get update && apt-get install -y iproute2 && tc qdisc add dev eth0 root netem delay 2000ms" 2>/dev/null

echo -e "${YELLOW}Network delay applied. Testing order creation...${NC}\n"

# Port forward and test
kubectl port-forward svc/order-service 5000:5000 &
PF_PID=$!
sleep 3

# Test with timing
echo -e "${YELLOW}Sending order request...${NC}"
START=$(date +%s%3N)
curl -X POST http://localhost:5000/orders \
  -H "Content-Type: application/json" \
  -d '{"product_id":"PROD-003","quantity":1,"email":"chaos@test.com"}' \
  -w "\n" -s

END=$(date +%s%3N)
DURATION=$((END - START))

echo -e "\n${GREEN}Response time: ${DURATION}ms${NC}"

# Cleanup
kill $PF_PID 2>/dev/null

echo -e "\n${RED}Removing network delay (pod will restart)...${NC}"
kubectl delete pod ${POD} --grace-period=0 --force

echo -e "${GREEN}✅ Chaos test complete${NC}\n"