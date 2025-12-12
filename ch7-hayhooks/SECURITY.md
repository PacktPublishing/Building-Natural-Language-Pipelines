# Security Setup for Hayhooks

This directory contains the nginx reverse proxy configuration that secures your Hayhooks API endpoints with authentication.

## Architecture

```
Client Request → nginx (Port 8080) → Authentication → Hayhooks (Internal Port 1416)
```

The Hayhooks service is NOT directly accessible from outside - only through the authenticated nginx proxy.

## Quick Setup

### 1. Generate Authentication Credentials

```bash
chmod +x scripts/generate_password.sh
./scripts/generate_password.sh
```

This creates `nginx/.htpasswd` with your username and password.

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### 3. Start the Secured Service

```bash
docker-compose up -d
```

### 4. Verify Setup

```bash
chmod +x scripts/test_secured_api.sh
./scripts/test_secured_api.sh
```

## Accessing the API

### Public Endpoints (No Authentication)

```bash
# Health check
curl http://localhost:8080/health

# Service status
curl http://localhost:8080/status
```

### Protected Endpoints (Authentication Required)

```bash
# Using basic auth
curl -u username:password http://localhost:8080/

# List pipelines
curl -u username:password http://localhost:8080/

# Run indexing pipeline
curl -u username:password \
  -X POST http://localhost:8080/indexing/run \
  -H "Content-Type: application/json" \
  -d '{"urls": ["https://example.com/article.pdf"]}'

# Run RAG query
curl -u username:password \
  -X POST http://localhost:8080/hybrid_rag/run \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the main topic?"}'
```

## Security Features

1. **Basic Authentication**: Username/password required for all pipeline endpoints
2. **Rate Limiting**: 10 requests/second per IP (configurable in nginx.conf)
3. **Network Isolation**: Hayhooks only accessible via nginx proxy
4. **Large Payload Support**: Handles up to 50MB uploads for PDFs
5. **Extended Timeouts**: 5-minute timeout for long-running pipelines

## Port Configuration

- **External Access**: Port 8080 (nginx)
- **Internal Only**: Port 1416 (hayhooks - not exposed)

## Managing Authentication

### Add New User

```bash
htpasswd nginx/.htpasswd newusername
```

### Change Password

```bash
htpasswd nginx/.htpasswd existingusername
```

### Remove User

Edit `nginx/.htpasswd` and delete the user's line.

### Restart After Changes

```bash
docker-compose restart nginx
```

## Monitoring

### View nginx logs

```bash
docker-compose logs -f nginx
```

### View Hayhooks logs

```bash
docker-compose logs -f hayhooks
```

### Check service health

```bash
# Nginx health
docker-compose exec nginx wget -q --spider http://localhost/health && echo "OK"

# Hayhooks health
curl http://localhost:8080/status
```

## Troubleshooting

### 401 Unauthorized

- Verify credentials: `cat nginx/.htpasswd`
- Regenerate: `./scripts/generate_password.sh`
- Check username/password in your request

### 502 Bad Gateway

- Check if Hayhooks is running: `docker-compose ps`
- View Hayhooks logs: `docker-compose logs hayhooks`
- Verify Hayhooks health: `docker-compose exec hayhooks curl localhost:1416/status`

### Rate Limiting (429 Too Many Requests)

- Adjust `limit_req_zone` in nginx.conf
- Restart: `docker-compose restart nginx`

## Production Considerations

### For Production Deployment:

1. **Use HTTPS**: Add SSL/TLS certificates
   ```nginx
   server {
       listen 443 ssl;
       ssl_certificate /path/to/cert.pem;
       ssl_certificate_key /path/to/key.pem;
   }
   ```

2. **Stronger Authentication**: Consider OAuth2/JWT instead of basic auth

3. **Environment Variables**: Store credentials securely (AWS Secrets Manager, etc.)

4. **Monitoring**: Add Prometheus/Grafana for metrics

5. **Backup**: Regularly backup `qdrant_storage` and `.htpasswd`

6. **Firewall**: Restrict access to known IP ranges

7. **Logging**: Configure log rotation and retention

## Nginx Configuration Reference

Key settings in `nginx.conf`:

- `limit_req_zone`: Rate limiting configuration
- `client_max_body_size`: Maximum upload size
- `proxy_*_timeout`: Timeout settings for long operations
- `auth_basic`: Authentication realm
- `auth_basic_user_file`: Password file location

## Comparison with Ch7 Pattern

**Ch7 (FastAPI)**:
- Uses `APIKeyHeader` dependency injection
- API key in `X-API-Key` header
- Validates against `RAG_API_KEY` environment variable

**Ch7-Hayhooks (nginx)**:
- Uses nginx basic authentication
- Credentials in username:password format
- Validates against `.htpasswd` file
- Additional rate limiting and request buffering

Both approaches provide similar security but adapted to their deployment architecture.
