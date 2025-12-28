# Deployment Guide

This guide covers how to deploy the Tiger Trader Bot and Dashboard using Docker.

## Prerequisites

- A server (Ubuntu 22.04 recommended) with at least **2 vCPUs** and **4GB RAM**.
- [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/) installed.

## 1. Server Setup

### Update System & Install Docker
```bash
sudo apt update && sudo apt upgrade -y
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
```

### Clone Repository
```bash
git clone https://github.com/yourusername/tiger_trader.git
cd tiger_trader
```

## 2. Configuration

**Crucial:** You must manually create the credential files on the server. These are not in the repository for security.

1. Create directory:
   ```bash
   mkdir -p credential
   ```

2. Create `credential/ds_api.txt`:
   ```bash
   # Paste your DeepSeek API Key (e.g. sk-...)
   nano credential/ds_api.txt
   ```

3. Create `credential/tiger_openapi_token.properties`:
   ```properties
   # Paste your Tiger Open API Token properties here
   tiger_id=...
   account=...
   token=...
   ```

4. Create `credential/tiger_openapi_config.properties`:
   ```properties
   # Basic Tiger Config
   tiger_id=YOUR_TIGER_ID
   account=YOUR_ACCOUNT_ID
   ```

5. Create `credential/private_key.pem`:
   ```bash
   # Paste your private key content (RSA Private Key)
   # It can start with -----BEGIN RSA PRIVATE KEY----- or just be the base64 content
   nano credential/private_key.pem
   ```

## 3. Deployment

Run the following command to build and start all services (Bot, API, Frontend):

```bash
sudo docker compose up -d --build
```

- **Backend API**: Running on port 8000 (internal).
- **Frontend Dashboard**: Running on port 80 (exposed).
- **Bot**: Running in the background.

## 4. Accessing the Dashboard

Open your browser and navigate to:
`http://<YOUR_SERVER_IP>`

## 5. Monitoring

View logs:
```bash
# All services
sudo docker compose logs -f

# Specific service
sudo docker compose logs -f bot
sudo docker compose logs -f backend
```

Stop services:
```bash
sudo docker compose down   
```

## Troubleshooting

- **Bot not trading?** Check `logs/errors.log` or `docker compose logs bot`.
- **Database issues?** The SQLite database is stored in `./data/trade.db`. Ensure permissions are correct (Docker usually handles this).
