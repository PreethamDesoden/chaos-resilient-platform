#!/bin/bash

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════╗"
echo "║   Chaos Resilience Testing Framework      ║"
echo "╚════════════════════════════════════════════╝"
echo -e "${NC}\n"

# Function to run test and log results
run_test() {
    TEST_NAME=$1
    TEST_CMD=$2
    
    echo -e "${YELLOW}Running: ${TEST_NAME}${NC}"
    echo "----------------------------------------"
    
    eval ${TEST_CMD}
    
    echo ""
    read -p "Press Enter to continue to next test..."
    echo ""
}

# Test 1: Pod Failure
run_test "Test 1: Random Pod Failure" "./pod-killer.sh"

# Test 2: Multiple Pod Failures
run_test "Test 2: Multiple Pod Failures (3 iterations)" "
    for i in {1..3}; do 
        echo 'Iteration $i';
        ./pod-killer.sh;
        sleep 5;
    done
"

# Test 3: Service availability during chaos
run_test "Test 3: Service Availability During Chaos" "
    kubectl port-forward svc/order-service 5000:5000 &
    PF_PID=\$!
    sleep 3
    
    for i in {1..5}; do
        echo 'Request \$i:'
        curl -X POST http://localhost:5000/orders \
          -H 'Content-Type: application/json' \
          -d '{\"product_id\":\"PROD-00\$i\",\"quantity\":1,\"email\":\"test@chaos.com\"}' \
          -w '\n' -s
        sleep 2
    done
    
    kill \$PF_PID 2>/dev/null
"

echo -e "${GREEN}"
echo "╔════════════════════════════════════════════╗"
echo "║   All Chaos Tests Complete!                ║"
echo "╚════════════════════════════════════════════╝"
echo -e "${NC}\n"

echo "Summary:"
kubectl get pods -o wide