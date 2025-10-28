#!/bin/bash

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Chaos Engineering: Pod Killer ===${NC}\n"

# Get all service pods
SERVICES=("order-service" "inventory-service" "notification-service")

# Randomly select a service
RANDOM_SERVICE=${SERVICES[$RANDOM % ${#SERVICES[@]}]}

echo -e "${YELLOW}Target Service: ${RANDOM_SERVICE}${NC}"

# Get all pods for that service
PODS=($(kubectl get pods -l app=${RANDOM_SERVICE} -o jsonpath='{.items[*].metadata.name}'))

if [ ${#PODS[@]} -eq 0 ]; then
    echo -e "${RED}No pods found for ${RANDOM_SERVICE}${NC}"
    exit 1
fi

# Randomly select a pod
RANDOM_POD=${PODS[$RANDOM % ${#PODS[@]}]}

echo -e "${RED}🔥 Killing pod: ${RANDOM_POD}${NC}"
echo -e "${YELLOW}Time: $(date '+%Y-%m-%d %H:%M:%S')${NC}\n"

# Record time before kill
START_TIME=$(date +%s)

# Kill the pod
kubectl delete pod ${RANDOM_POD} --grace-period=0 --force

echo -e "\n${YELLOW}Waiting for replacement pod to be ready...${NC}"

# Wait for new pod to be ready
sleep 5

NEW_PODS=($(kubectl get pods -l app=${RANDOM_SERVICE} -o jsonpath='{.items[*].metadata.name}'))

# Find the new pod (different name)
for pod in "${NEW_PODS[@]}"; do
    if [[ ! " ${PODS[@]} " =~ " ${pod} " ]]; then
        NEW_POD=${pod}
        break
    fi
done

# Wait for pod to be ready
kubectl wait --for=condition=ready pod/${NEW_POD} --timeout=60s

END_TIME=$(date +%s)
RECOVERY_TIME=$((END_TIME - START_TIME))

echo -e "\n${GREEN}✅ Recovery complete!${NC}"
echo -e "${GREEN}New pod: ${NEW_POD}${NC}"
echo -e "${GREEN}Recovery time: ${RECOVERY_TIME} seconds${NC}\n"

# Verify service is healthy
echo -e "${YELLOW}Verifying service health...${NC}"
kubectl get pods -l app=${RANDOM_SERVICE}