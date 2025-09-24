#!/bin/bash

set -e

echo "🧹 Tearing down IAM MCP Server from local Kubernetes"

# PID file location for tracking port-forward process
PID_DIR="${HOME}/.local/share/iam-mcp-server"
PID_FILE="${PID_DIR}/port-forward.pid"
PORT_FILE="${PID_DIR}/port-forward.port"

# Check if kubectl is available
if ! command -v kubectl &> /dev/null; then
    echo "❌ kubectl not found. Please install kubectl first."
    exit 1
fi

# Check if connected to docker-desktop context
CURRENT_CONTEXT=$(kubectl config current-context)
if [[ "$CURRENT_CONTEXT" != "docker-desktop" ]]; then
    echo "⚠️  Current context is '$CURRENT_CONTEXT', switching to 'docker-desktop'"
    kubectl config use-context docker-desktop
fi

# Delete namespace (this will delete everything in it)
echo "🗑️  Deleting namespace 'mcp' and all resources..."
kubectl delete namespace mcp --ignore-not-found=true --wait=true --timeout=30s 2>/dev/null || true

# Clean up port-forward process using PID file
echo "🔌 Cleaning up port-forward processes..."

# First, try to clean up using PID file (preferred method)
if [ -f "$PID_FILE" ]; then
    PF_PID=$(cat "$PID_FILE" 2>/dev/null || echo "")
    PORT=$(cat "$PORT_FILE" 2>/dev/null || echo "unknown")

    if [ -n "$PF_PID" ]; then
        if kill -0 "$PF_PID" 2>/dev/null; then
            echo "   Stopping port-forward (PID: $PF_PID, Port: $PORT)..."
            kill "$PF_PID" 2>/dev/null || true
            sleep 1

            # Force kill if still running
            if kill -0 "$PF_PID" 2>/dev/null; then
                echo "   Force stopping port-forward..."
                kill -9 "$PF_PID" 2>/dev/null || true
            fi
        else
            echo "   Port-forward process (PID: $PF_PID) not running"
        fi
    fi

    # Clean up PID files
    rm -f "$PID_FILE" "$PORT_FILE"
fi

# Fallback: Kill any remaining kubectl port-forward processes
echo "   Cleaning up any remaining port-forward processes..."
pkill -f "kubectl port-forward.*mcp" 2>/dev/null || true
# Give processes time to terminate
sleep 1

# Optional: Remove Docker images
read -p "❓ Do you want to remove Docker images? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "🗑️  Removing Docker images..."
    docker rmi iam-mcp-server:latest 2>/dev/null || true
    docker rmi docker.io/library/iam-mcp-server:latest 2>/dev/null || true
    docker rmi iam-mcp-server:dev 2>/dev/null || true
fi

echo "✅ Teardown complete!"
echo ""
echo "You can now run ./deploy-local.sh to redeploy"