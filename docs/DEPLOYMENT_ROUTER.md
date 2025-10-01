# Deploying the Natural Language → TOPdesk MCP Router

## Prerequisites

1. **Python 3.11+** installed on the target system
2. **TOPdesk MCP Server** running and accessible
3. **Network connectivity** between router and MCP server

## Installation

### Option 1: Direct Installation

```bash
# Clone the repository
git clone https://github.com/SeeITBV/Topdesk_MCP_python.git
cd Topdesk_MCP_python

# Install the package with router dependencies
pip install -e .

# Or with development tools
pip install -e ".[dev]"
```

### Option 2: Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Copy requirements and install dependencies
COPY pyproject.toml .
RUN pip install -e .

# Copy application code
COPY app/ app/
COPY .env.nl-router .env

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Configuration

### Environment Variables

Create a `.env` file based on `.env.nl-router`:

```env
# Required
MCP_BASE_URL=http://your-mcp-server:3030
MCP_API_KEY=your-api-key-if-needed

# Optional
LOG_LEVEL=INFO
RATE_LIMIT_REQUESTS=60
RATE_LIMIT_WINDOW=300
MCP_TIMEOUT=8
MCP_RETRIES=2
```

### Key Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_BASE_URL` | Required | URL where your TOPdesk MCP server is running |
| `MCP_API_KEY` | Optional | API key if MCP server requires authentication |
| `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `RATE_LIMIT_REQUESTS` | 60 | Max requests per client per time window |
| `RATE_LIMIT_WINDOW` | 300 | Rate limit time window in seconds |
| `CIRCUIT_BREAKER_FAILURE_THRESHOLD` | 5 | Failures before circuit opens |
| `MCP_TIMEOUT` | 8 | Request timeout in seconds |
| `MAX_ALLOWED_RESULTS` | 25 | Maximum results per query |

## Running the Service

### Development Mode

```bash
# Using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Using the example script
python example_usage.py
```

### Production Mode

```bash
# Basic production run
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# With gunicorn (recommended)
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Docker Compose

```yaml
version: '3.8'

services:
  nl-router:
    build: .
    ports:
      - "8000:8000"
    environment:
      - MCP_BASE_URL=http://mcp-server:3030
      - LOG_LEVEL=INFO
    depends_on:
      - mcp-server
    restart: unless-stopped

  mcp-server:
    # Your existing TOPdesk MCP server configuration
    # ...
```

## Testing the Deployment

### Health Checks

```bash
# Basic health check
curl http://localhost:8000/health

# Detailed status
curl http://localhost:8000/status

# Service info
curl http://localhost:8000/
```

### Example API Calls

```bash
# Simple query
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "email problems", "max_results": 5}'

# Person-specific query
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "tickets for John Doe", "max_results": 10}'

# Complex query
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "high priority open incidents from last week", "max_results": 15}'
```

## Production Considerations

### Reverse Proxy (nginx)

```nginx
upstream nl_router {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://nl_router;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

### Systemd Service

Create `/etc/systemd/system/nl-router.service`:

```ini
[Unit]
Description=Natural Language TOPdesk MCP Router
After=network.target

[Service]
Type=exec
User=app
Group=app
WorkingDirectory=/opt/nl-router
Environment=PATH=/opt/nl-router/venv/bin
ExecStart=/opt/nl-router/venv/bin/gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
ExecReload=/bin/kill -HUP $MAINPID
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable nl-router
sudo systemctl start nl-router
```

### Monitoring

Monitor these key metrics:

1. **Response Times**: Check `X-Process-Time` header
2. **Rate Limiting**: Monitor `X-RateLimit-*` headers
3. **Circuit Breaker**: Check `/status` endpoint
4. **Error Rates**: Monitor application logs
5. **MCP Connectivity**: Monitor `/health` endpoint

### Log Management

```bash
# Rotate logs
sudo logrotate -d /etc/logrotate.d/nl-router

# Log configuration in /etc/logrotate.d/nl-router:
/var/log/nl-router/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 644 app app
    postrotate
        systemctl reload nl-router
    endscript
}
```

## Security Hardening

### API Security

1. **Authentication**: Add API key authentication if needed
2. **CORS**: Configure CORS policy for your domain
3. **Rate Limiting**: Tune rate limits based on usage
4. **Input Validation**: All inputs are validated (already implemented)

### Network Security

1. **Firewall**: Only allow necessary ports
2. **TLS**: Use HTTPS in production
3. **VPN**: Consider VPN for internal services
4. **Network Segmentation**: Isolate services appropriately

### Environment Security

```bash
# Secure .env file
chmod 600 .env
chown app:app .env

# Run as non-root user
useradd -r -s /bin/false app
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   ```bash
   # Check if MCP server is running
   curl http://your-mcp-server:3030/health
   
   # Check firewall
   sudo ufw status
   ```

2. **Rate Limiting Issues**
   ```bash
   # Check rate limit status
   curl -I http://localhost:8000/ask
   
   # Adjust in .env
   RATE_LIMIT_REQUESTS=120
   ```

3. **Circuit Breaker Open**
   ```bash
   # Check circuit breaker status
   curl http://localhost:8000/status
   
   # Wait for recovery or restart service
   sudo systemctl restart nl-router
   ```

4. **High Memory Usage**
   ```bash
   # Monitor memory
   htop
   
   # Reduce workers or add memory limits
   gunicorn --max-requests 1000 --max-requests-jitter 100
   ```

### Log Analysis

```bash
# Check application logs
tail -f /var/log/nl-router/app.log

# Filter for errors
grep ERROR /var/log/nl-router/app.log

# Monitor specific queries
grep "query_intent" /var/log/nl-router/app.log
```

## Backup and Recovery

### Configuration Backup

```bash
# Backup configuration
tar -czf nl-router-config-$(date +%Y%m%d).tar.gz .env app/

# Restore configuration
tar -xzf nl-router-config-*.tar.gz
```

### Health Monitoring Script

```bash
#!/bin/bash
# health-check.sh

ENDPOINT="http://localhost:8000/health"
TIMEOUT=10

if curl -s --max-time $TIMEOUT $ENDPOINT | grep -q "healthy"; then
    echo "Service is healthy"
    exit 0
else
    echo "Service is unhealthy"
    # Restart service
    sudo systemctl restart nl-router
    exit 1
fi
```

## Performance Tuning

### Optimization Settings

```env
# Increase timeouts for complex queries
MCP_TIMEOUT=15
MCP_RETRIES=3

# Adjust rate limiting for high-traffic
RATE_LIMIT_REQUESTS=120
RATE_LIMIT_WINDOW=300

# Circuit breaker tuning
CIRCUIT_BREAKER_FAILURE_THRESHOLD=10
CIRCUIT_BREAKER_RECOVERY_TIMEOUT=30
```

### Resource Requirements

**Minimum Requirements:**
- CPU: 1 core
- RAM: 512MB
- Disk: 1GB
- Network: 10Mbps

**Recommended for Production:**
- CPU: 2-4 cores
- RAM: 2-4GB
- Disk: 10GB (for logs)
- Network: 100Mbps

## Support

For issues and questions:
- Check the main [README_NL_ROUTER.md](README_NL_ROUTER.md)
- Review logs for error details  
- Test with the `example_usage.py` script
- Open an issue on the GitHub repository