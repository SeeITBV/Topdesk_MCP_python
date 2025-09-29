FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy application files
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -e .

# Create non-root user
RUN groupadd -r topdesk && useradd -r -g topdesk topdesk
RUN chown -R topdesk:topdesk /app
USER topdesk

# Expose port for HTTP transport
EXPOSE 3030

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:3030/health', timeout=5)" || exit 1

# Default to HTTP transport for container deployment
ENV TOPDESK_MCP_TRANSPORT=streamable-http
ENV TOPDESK_MCP_HOST=0.0.0.0
ENV TOPDESK_MCP_PORT=3030

# Use exec form to ensure proper signal handling
CMD ["python", "-m", "topdesk_mcp.main"]