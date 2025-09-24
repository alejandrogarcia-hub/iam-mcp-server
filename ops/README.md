# IAM MCP Server - Production Deployment

This directory contains configuration for deploying the IAM MCP Server to production environments.

## Architecture

The MCP server can be deployed in two modes:

1. **stdio mode**: For local development and Claude Desktop integration
2. **HTTP/SSE mode**: For production deployment as a web service

## Deployment Options

### 1. Docker Standalone

```bash
# Build the image
docker build -t iam-mcp-server:latest .

# Run in stdio mode (for testing)
docker run --rm -i \
  -e RAPIDAPI_KEY="your-api-key" \
  -e LOG_LEVEL=INFO \
  iam-mcp-server:latest

# Run in HTTP/SSE mode (for production)
docker run -d \
  -p 8080:8080 \
  -e RAPIDAPI_KEY="your-api-key" \
  -e LOG_LEVEL=INFO \
  --name iam-mcp-server \
  iam-mcp-server:latest \
  mcp_server_iam.server_http
```

### 2. Kubernetes Deployment

#### Prerequisites

- Kubernetes cluster (1.19+)
- kubectl configured
- Container registry for Docker images (production) or Docker Desktop (local)

#### Local Development with Docker Desktop Kubernetes

For local testing on macOS with Docker Desktop:

1. **Enable Kubernetes in Docker Desktop:**
   - Open Docker Desktop preferences
   - Navigate to Kubernetes tab
   - Check "Enable Kubernetes"
   - Click "Apply & Restart"

2. **Deploy using the automated script:**

   ```bash
   # Make sure you're in the project root
   cd /path/to/iam-mcp-server

   # Set your RapidAPI key (optional, uses test key if not set)
   export RAPIDAPI_KEY="your-api-key"

   # Run the deployment script (default port 9999)
   ./ops/k8s/deploy-local.sh

   # Or specify a custom port
   ./ops/k8s/deploy-local.sh 8888
   ```

   The script will:
   - Build the Docker image locally
   - Auto-detect Docker Desktop node names (compatible across versions)
   - Load image to Kubernetes nodes if possible (fallback to Docker daemon)
   - Create the namespace and secrets
   - Deploy the server
   - Start port forwarding in the background (silently)
   - Save the process ID for clean teardown
   - Exit cleanly (non-blocking)

   **Port Management:**
   - Default port: 9999
   - Custom port: Pass as first argument (must be 1024-65535)
   - Process ID saved to: `~/.local/share/iam-mcp-server/port-forward.pid`
   - Port number saved to: `~/.local/share/iam-mcp-server/port-forward.port`

3. **Teardown deployment:**

   ```bash
   # Remove all resources
   ./ops/k8s/teardown-local.sh
   ```

   This script will:
   - Delete the namespace and all resources
   - Stop the port-forward process using saved PID
   - Clean up PID and port files
   - Fallback to pkill for any orphaned processes
   - Optionally remove Docker images

#### Production Deployment

1. **Build and push Docker image:**

   ```bash
   docker build -t your-registry/iam-mcp-server:latest .
   docker push your-registry/iam-mcp-server:latest
   ```

2. **Update configuration:**
   - Edit `k8s/deployment.yaml` to set your image registry
   - Update `k8s/ingress.yaml` with your domain
   - Set your RapidAPI key in `k8s/deployment.yaml` secret

3. **Deploy to Kubernetes:**

   ```bash
   # Create namespace
   kubectl apply -f ops/k8s/namespace.yaml

   # Deploy all resources
   kubectl apply -f ops/k8s/

   # Or use kustomize
   kubectl apply -k ops/k8s/
   ```

4. **Verify deployment:**

   ```bash
   kubectl get pods -n mcp
   kubectl logs -n mcp -l app=iam-mcp-server
   ```

### 3. Docker Compose (Development)

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  iam-mcp-server:
    image: iam-mcp-server:latest
    command: ["mcp_server_iam.server_http"]
    ports:
      - "8080:8080"
    environment:
      - RAPIDAPI_KEY=${RAPIDAPI_KEY}
      - LOG_LEVEL=INFO
      - CORS_ORIGINS=*
    volumes:
      - ./data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 3s
      retries: 3
```

## Transport Protocols

### HTTP/SSE Transport

The production server uses HTTP POST for client-to-server and Server-Sent Events (SSE) for server-to-client communication:

- **Endpoint**: `/messages` (HTTP POST) - For sending MCP protocol messages
- **SSE Endpoint**: `/sse` (GET) - For receiving streaming responses
- **Health Check**: `/health` (GET) - For monitoring server status

SSE (Server-Sent Events) enables real-time, unidirectional communication from server to client over HTTP. The MCP server uses SSE to stream responses back to clients, allowing for:

- Real-time updates during long-running operations
- Streaming of partial results as they become available
- Efficient handling of asynchronous server notifications

### Testing HTTP Interaction

#### Health Check

```bash
# Check if the server is running
curl http://localhost:9999/health
# Response: {"status":"healthy","service":"iam-mcp-server"}
```

#### Complete MCP Session Flow with HTTP/SSE

The HTTP/SSE transport requires establishing a session first, then using that session ID for all requests:

##### Step 1: Get Session ID from SSE

```bash
# Connect to SSE endpoint to get a session ID
curl -N -H "Accept: text/event-stream" "http://localhost:9999/sse"
# Response will include:
# event: endpoint
# data: /messages/?session_id=YOUR_SESSION_ID
```

##### Step 2: Initialize MCP Session

```bash
# Initialize request (use the session ID from step 1)
curl -X POST "http://localhost:9999/messages/?session_id=YOUR_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"initialize","params":{"protocolVersion":"0.1.0","capabilities":{"prompts":{},"tools":{}},"clientInfo":{"name":"test-client","version":"1.0.0"}},"id":1}'
# Response: "Accepted" (actual response comes via SSE)

# Send initialized notification (required by MCP protocol)
curl -X POST "http://localhost:9999/messages/?session_id=YOUR_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"notifications/initialized","params":{"capabilities":{}}}'
# Response: "Accepted"
```

#### List Available Prompts

```bash
# List all available prompts (use session ID from SSE)
curl -X POST "http://localhost:9999/messages/?session_id=YOUR_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"prompts/list","params":{},"id":2}'
# Response: "Accepted" (actual list comes via SSE)
```

#### List Available Tools

```bash
# List all available tools (use session ID from SSE)
curl -X POST "http://localhost:9999/messages/?session_id=YOUR_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","params":{},"id":3}'
# Response: "Accepted" (actual list comes via SSE)
```

#### Call a Tool (Example: Search Jobs)

```bash
# Search for Python developer jobs (use session ID from SSE)
curl -X POST "http://localhost:9999/messages/?session_id=YOUR_SESSION_ID" \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"search_jobs","arguments":{"query":"Python developer","location":"San Francisco, CA","num_pages":1}},"id":4}'
# Response: "Accepted" (actual results come via SSE)
```

#### Using SSE for Streaming Responses

SSE provides a persistent connection for receiving server events:

```bash
# Connect to SSE endpoint for real-time updates
curl -N -H "Accept: text/event-stream" http://localhost:9999/sse

# The connection will remain open, streaming events as they occur
# Events are formatted as:
# event: message
# data: {"jsonrpc":"2.0","method":"...","params":{...}}
#
# event: message
# data: {"jsonrpc":"2.0","result":{...},"id":1}
```

For interactive testing with SSE, you can use two terminals:

1. Terminal 1: Connect to SSE endpoint to receive streaming responses
2. Terminal 2: Send requests to `/messages` endpoint

Example SSE client in Python:

```python
import sseclient
import requests

# Connect to SSE endpoint
response = requests.get('http://localhost:9999/sse', stream=True)
client = sseclient.SSEClient(response)

# Process incoming events
for event in client.events():
    print(f"Event: {event.event}")
    print(f"Data: {event.data}")
```

### Connecting MCP Clients

#### Claude Desktop Connection (HTTP/SSE)

After deploying to Kubernetes with port-forward on localhost:9999:

1. **Open Claude Desktop** (Pro, Max, Team, or Enterprise plan required)
2. **Navigate to Settings > Connectors**
3. **Click "Add custom connector"** at the bottom
4. **Enter the MCP server URL:**
   - For local Kubernetes: `http://localhost:9999`
   - For production: `https://your-domain.com`
5. **Optional:** Configure authentication in "Advanced settings"
6. **Click "Add"** to save

**Important:**

- HTTP/SSE connectors are configured via Settings > Connectors, NOT in `claude_desktop_config.json`
- This feature is currently in beta
- The server must be running and accessible at the specified URL
- For local testing, ensure `kubectl port-forward` is active

#### From Another Service (Kubernetes)

```python
import httpx
from mcp import Client

# Connect to the MCP server
client = Client(
    url="http://iam-mcp-server.mcp.svc.cluster.local/messages",
    transport="http"
)

# Initialize
await client.initialize()

# Use the MCP server
tools = await client.list_tools()
```

#### From External Client

```javascript
// Using MCP SDK
import { Client } from '@modelcontextprotocol/sdk';

const client = new Client({
  url: 'https://mcp.your-domain.com/messages',
  transport: 'sse'
});

await client.initialize();
const prompts = await client.listPrompts();
```

## Security Considerations

### API Keys

- Store API keys in Kubernetes Secrets
- Use environment variables, never hardcode
- Rotate keys regularly

### Network Security

- Use TLS/SSL for external connections
- Configure CORS appropriately (restrict origins in production)
- Use NetworkPolicies to restrict pod-to-pod communication

### CORS Configuration

The server handles CORS at the application level. Set the `CORS_ORIGINS` environment variable:

- `CORS_ORIGINS=*` - Allow all origins (development only)
- `CORS_ORIGINS=https://app.example.com,https://admin.example.com` - Allow specific origins (production)
- Omit `CORS_ORIGINS` - CORS middleware not applied (when handled by ingress/proxy)

For production, consider handling CORS at the ingress level instead for better performance.

### Resource Limits

- Set appropriate CPU/memory limits
- Configure autoscaling based on load
- Use PodDisruptionBudgets for high availability

## Monitoring

### Health Checks

The server exposes `/health` endpoint for monitoring:

```bash
curl http://localhost:8080/health
```

### Logs

```bash
# Kubernetes
kubectl logs -n mcp -l app=iam-mcp-server -f

# Docker
docker logs -f iam-mcp-server
```

### Metrics (Optional)

Consider adding Prometheus metrics:

- Request count
- Response times
- Error rates
- Active connections

## Scaling

### Horizontal Scaling

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: iam-mcp-server
  namespace: mcp
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: iam-mcp-server
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
```

### Session Affinity

For SSE connections, enable session affinity in the Service:

```yaml
spec:
  sessionAffinity: ClientIP
  sessionAffinityConfig:
    clientIP:
      timeoutSeconds: 3600
```

## Troubleshooting

### Common Issues

1. **Connection refused**: Check if the server is running and ports are exposed
2. **CORS errors**: Verify CORS_ORIGINS environment variable
3. **SSE timeout**: Increase proxy timeouts in Ingress
4. **Authentication errors**: Check RAPIDAPI_KEY is set correctly
5. **Port already in use**:
   - Check for existing port-forward: `cat ~/.local/share/iam-mcp-server/port-forward.pid`
   - Kill existing process: `kill $(cat ~/.local/share/iam-mcp-server/port-forward.pid)`
   - Or use a different port: `./ops/k8s/deploy-local.sh 8888`
6. **Port-forward not working**:
   - Check if process is running: `ps aux | grep port-forward`
   - Check PID file exists: `ls -la ~/.local/share/iam-mcp-server/`
   - Manually start port-forward: `kubectl port-forward -n mcp svc/iam-mcp-server 9999:80`

### Debug Mode

Enable debug logging:

```bash
-e LOG_LEVEL=DEBUG
```

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy MCP Server
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2

      - name: Build and push Docker image
        run: |
          docker build -t ${{ secrets.REGISTRY }}/iam-mcp-server:${{ github.sha }} .
          docker push ${{ secrets.REGISTRY }}/iam-mcp-server:${{ github.sha }}

      - name: Deploy to Kubernetes
        run: |
          kubectl set image deployment/iam-mcp-server \
            iam-mcp-server=${{ secrets.REGISTRY }}/iam-mcp-server:${{ github.sha }} \
            -n mcp
```
