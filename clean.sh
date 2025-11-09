#!/bin/bash

echo "⚠️  This will DELETE the entire cluster and all data!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "Cancelled."
    exit 0
fi

echo ""
echo "🗑️  Deleting cluster..."
kind delete cluster --name chaos-platform

echo "🧹 Cleaning up..."
pkill -f "port-forward" > /dev/null 2>&1
sudo systemctl stop jenkins > /dev/null 2>&1

echo ""
echo "✅ Everything deleted!"
echo "Run ./start.sh to recreate from scratch"
