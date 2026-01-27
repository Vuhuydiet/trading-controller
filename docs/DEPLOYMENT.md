# DigitalOcean Deployment Guide

## Chi phí ước tính (10 ngày)

| Resource | Spec | Cost/month | Cost/10 days |
|----------|------|------------|--------------|
| Droplet | 8GB RAM / 4 vCPU | $48 | ~$16 |
| **Total** | | | **~$16** |

Với budget $50, bạn còn dư ~$34 dự phòng.

---

## Bước 1: Tạo DigitalOcean Droplet

1. Đăng nhập [DigitalOcean](https://cloud.digitalocean.com/)
2. Click **Create** → **Droplets**
3. Chọn:
   - **Region**: Singapore (gần VN nhất)
   - **Image**: Ubuntu 24.04 LTS
   - **Size**: Basic → Regular → **8GB / 4 vCPU** ($48/mo)
   - **Authentication**: SSH Key (khuyến nghị) hoặc Password
4. Click **Create Droplet**
5. Copy IP address

---

## Bước 2: SSH vào Server

```bash
ssh root@YOUR_DROPLET_IP
```

---

## Bước 3: Cài đặt Docker

```bash
# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose-plugin -y

# Verify installation
docker --version
docker compose version
```

---

## Bước 4: Clone Project

```bash
# Install git
apt install git -y

# Clone repo
cd /opt
git clone https://github.com/YOUR_USERNAME/trading-controller.git
cd trading-controller
```

---

## Bước 5: Cấu hình Environment

```bash
# Copy và edit .env
cp .env.production .env
nano .env
```

**Chỉnh sửa các giá trị:**
```env
SECRET_KEY=generate-a-random-string-here
CORS_ORIGINS=["http://localhost:3000", "https://your-frontend.com"]
```

Tạo SECRET_KEY:
```bash
openssl rand -hex 32
```

---

## Bước 6: Tạo thư mục data

```bash
mkdir -p data logs
chmod 777 data logs
```

---

## Bước 7: Build và Start Services

```bash
# Build images
docker compose build

# Start services (API + Kafka + Ollama)
docker compose up -d

# Check logs
docker compose logs -f
```

---

## Bước 8: Pull Ollama Model

```bash
# Pull llama3.2 model (khoảng 2GB, mất vài phút)
docker exec -it ollama ollama pull llama3.2

# Verify
docker exec -it ollama ollama list
```

---

## Bước 9: Verify Deployment

```bash
# Check all services running
docker compose ps

# Test API
curl http://localhost:8000/health
curl http://localhost:8000/docs

# Test từ bên ngoài
curl http://YOUR_DROPLET_IP:8000/health
```

---

## Bước 10: (Optional) Chạy Crawler

```bash
# Start crawler service
docker compose --profile crawler up -d

# Check crawler logs
docker compose logs -f crawler
```

---

## Firewall Setup

```bash
# Allow necessary ports
ufw allow 22    # SSH
ufw allow 8000  # API
ufw enable
```

---

## Useful Commands

```bash
# View logs
docker compose logs -f api
docker compose logs -f kafka
docker compose logs -f ollama

# Restart services
docker compose restart

# Stop all
docker compose down

# Stop and remove volumes (CAUTION: deletes data)
docker compose down -v

# Rebuild and restart
docker compose up -d --build

# Enter container shell
docker exec -it trading-api bash
docker exec -it ollama bash
```

---

## API Endpoints for Frontend

Base URL: `http://YOUR_DROPLET_IP:8000`

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/docs` | GET | Swagger UI |
| `/api/v1/news` | GET | Get news list |
| `/api/v1/news/{id}` | GET | Get news detail |
| `/api/v1/news/symbol/{symbol}` | GET | News by symbol |
| `/api/v1/market/ticker/{symbol}` | GET | Get ticker |
| `/api/v1/market/klines/{symbol}` | GET | Get candlesticks |
| `/api/v1/analysis/sentiment/{symbol}` | GET | AI sentiment |

---

## Troubleshooting

### API không start được
```bash
docker compose logs api
# Check nếu Kafka chưa ready
docker compose restart api
```

### Ollama không connect được
```bash
# Check Ollama status
docker exec -it ollama ollama list

# Nếu chưa có model
docker exec -it ollama ollama pull llama3.2
```

### Kafka issues
```bash
# Restart Kafka
docker compose restart kafka

# Check logs
docker compose logs kafka
```

### Out of memory
```bash
# Check memory usage
docker stats

# Nếu cần, tăng swap
fallocate -l 4G /swapfile
chmod 600 /swapfile
mkswap /swapfile
swapon /swapfile
echo '/swapfile none swap sw 0 0' >> /etc/fstab
```

---

## Quick Deploy Script

Tạo file `deploy.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Starting deployment..."

# Pull latest code
git pull origin main

# Build and restart
docker compose build
docker compose up -d

# Wait for services
echo "⏳ Waiting for services to start..."
sleep 30

# Pull Ollama model if not exists
docker exec ollama ollama pull llama3.2 2>/dev/null || true

# Health check
curl -f http://localhost:8000/health && echo "✅ API is healthy!"

echo "🎉 Deployment complete!"
```

```bash
chmod +x deploy.sh
./deploy.sh
```
