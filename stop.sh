#!/bin/bash

echo "🛑 Stopping Chaos-Resilient Platform..."
echo ""

# Kill port forwards
echo "🔌 Stopping port-forwards..."
pkill -f "port-forward" > /dev/null 2>&1

# Stop Jenkins
echo "⚙️  Stopping Jenkins..."
sudo systemctl stop jenkins > /dev/null 2>&1

# Stop KIND cluster (keeps data)
echo "📦 Stopping cluster..."
docker stop chaos-platform-control-plane > /dev/null 2>&1

echo ""
echo "✅ All stopped!"
echo ""
echo "To start again: ./start.sh"
