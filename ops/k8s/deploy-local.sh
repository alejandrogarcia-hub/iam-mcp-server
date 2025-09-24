#!/bin/bash

set -e

# Parse command line arguments
PORT=${1:-9999}
if ! [[ "$PORT" =~ ^[0-9]+$ ]] || [ "$PORT" -lt 1024 ] || [ "$PORT" -gt 65535 ]; then
    echo "❌ Invalid port number: $PORT (must be between 1024 and 65535)"
    exit 1
fi

# PID file location for tracking port-forward process
PID_DIR="${HOME}/.local/share/iam-mcp-server"
PID_FILE="${PID_DIR}/port-forward.pid"
PORT_FILE="${PID_DIR}/port-forward.port"

echo "🚀 Deploying IAM MCP Server to local Kubernetes (Docker Desktop)"
echo "   Port: $PORT"
echo ""

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

# Clean up any existing deployment first
echo "🧹 Cleaning up any existing deployment..."
kubectl delete deployment iam-mcp-server -n mcp --ignore-not-found=true 2>/dev/null || true

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t iam-mcp-server:latest .

# Check if image was built
if ! docker images | grep -q "iam-mcp-server.*latest"; then
    echo "❌ Failed to build Docker image"
    exit 1
fi

# For Docker Desktop Kubernetes, we need to load the image to the cluster nodes
echo "🏷️  Loading image into Docker Desktop Kubernetes cluster..."

# Try to detect Docker Desktop node names (they vary across versions)
CONTROL_PLANE_NODE=""
WORKER_NODE=""

# Common node name patterns for Docker Desktop
POSSIBLE_CONTROL_PLANES=("desktop-control-plane" "docker-desktop" "docker-for-desktop")
POSSIBLE_WORKERS=("desktop-worker" "docker-desktop-worker")

# Try to find control plane node
for node in "${POSSIBLE_CONTROL_PLANES[@]}"; do
    if docker ps -q -f name="^${node}$" 2>/dev/null | grep -q .; then
        CONTROL_PLANE_NODE="$node"
        echo "   Found control plane node: $node"
        break
    fi
done

# Try to find worker node
for node in "${POSSIBLE_WORKERS[@]}"; do
    if docker ps -q -f name="^${node}$" 2>/dev/null | grep -q .; then
        WORKER_NODE="$node"
        echo "   Found worker node: $node"
        break
    fi
done

# Load image to nodes if found, otherwise skip (will use local Docker daemon)
if [ -n "$CONTROL_PLANE_NODE" ]; then
    echo "   Loading image to control plane..."
    docker save iam-mcp-server:latest | docker exec -i "$CONTROL_PLANE_NODE" ctr --namespace=k8s.io images import - 2>/dev/null || {
        echo "   ⚠️  Could not load to control plane, will rely on local Docker daemon"
    }
else
    echo "   ⚠️  Control plane node not found, will rely on local Docker daemon"
fi

if [ -n "$WORKER_NODE" ]; then
    echo "   Loading image to worker node..."
    docker save iam-mcp-server:latest | docker exec -i "$WORKER_NODE" ctr --namespace=k8s.io images import - 2>/dev/null || {
        echo "   ⚠️  Could not load to worker node, will rely on local Docker daemon"
    }
fi

# For newer Docker Desktop versions, the image might already be available
# via the shared Docker daemon, so we don't fail if loading doesn't work

# Set your RapidAPI key
if [ -z "$RAPIDAPI_KEY" ]; then
    echo "⚠️  RAPIDAPI_KEY not set. Using test key."
    echo "   To use your actual key: export RAPIDAPI_KEY='your-key'"
    RAPIDAPI_KEY="test-api-key"
fi

# Deploy using simple kubectl approach
echo "📦 Deploying to Kubernetes..."

# Apply namespace (will skip if already exists)
kubectl apply -f ops/k8s/namespace.yaml 2>/dev/null || true

# Create/update secret
kubectl delete secret iam-mcp-secrets -n mcp 2>/dev/null || true
kubectl create secret generic iam-mcp-secrets -n mcp --from-literal=rapidapi-key="$RAPIDAPI_KEY"

# Apply local deployment (with imagePullPolicy: Never already set)
kubectl apply -f ops/k8s/deployment-local.yaml

# Wait for deployment
echo "⏳ Waiting for deployment to be ready..."
if kubectl wait --for=condition=available --timeout=60s deployment/iam-mcp-server -n mcp; then
    # Get pod status
    echo "✅ Deployment complete!"
    echo ""
    kubectl get pods -n mcp

    # Port forward for testing
    echo ""
    echo "📡 Setting up port forwarding..."

    # Clean up any existing port-forward from previous run
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE" 2>/dev/null || echo "")
        if [ -n "$OLD_PID" ] && kill -0 "$OLD_PID" 2>/dev/null; then
            echo "   Stopping existing port-forward (PID: $OLD_PID)..."
            kill "$OLD_PID" 2>/dev/null || true
            sleep 1
        fi
    fi

    # Check if port is already in use
    if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null 2>&1; then
        echo "❌ Port $PORT is already in use!"
        echo "   Please free the port or run: lsof -i :$PORT"
        exit 1
    fi

    # Create PID directory if it doesn't exist
    mkdir -p "$PID_DIR"

    # Start port-forward in background with output redirected
    kubectl port-forward -n mcp service/iam-mcp-server $PORT:80 > /dev/null 2>&1 &
    PF_PID=$!

    # Save PID and port to files
    echo "$PF_PID" > "$PID_FILE"
    echo "$PORT" > "$PORT_FILE"

    # Wait a moment to ensure port-forward starts
    sleep 2

    # Check if port-forward is still running
    if ! kill -0 "$PF_PID" 2>/dev/null; then
        echo "❌ Port forwarding failed to start"
        rm -f "$PID_FILE" "$PORT_FILE"
        exit 1
    fi

    echo "✅ Port forwarding started successfully (PID: $PF_PID)"
    echo ""
    echo "   🌐 Access the server at: http://localhost:$PORT"
    echo "   🏥 Health check: http://localhost:$PORT/health"
    echo "   📝 SSE endpoint: http://localhost:$PORT/sse"
    echo ""
    echo "   To stop port forwarding, run:"
    echo "   ./ops/k8s/teardown-local.sh"
    echo ""
    echo "   Or manually:"
    echo "   kill $PF_PID"
else
    echo "❌ Deployment failed to become ready"
    echo ""
    echo "Checking pod status:"
    kubectl get pods -n mcp
    echo ""
    echo "Checking pod events:"
    kubectl describe pod -n mcp -l app=iam-mcp-server | grep -A 10 "Events:" || true
    echo ""
    echo "Checking logs (if available):"
    kubectl logs -n mcp -l app=iam-mcp-server --tail=20 2>/dev/null || echo "No logs available yet"
    exit 1
fi