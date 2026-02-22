# 🚀 AI Agent System - Deployment Guide

Production deployment guide for the AI Agent System v2.0

---

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Server Setup](#server-setup)
- [Backend Deployment](#backend-deployment)
- [Frontend Deployment](#frontend-deployment)
- [Systemd Services](#systemd-services)
- [Nginx Configuration](#nginx-configuration)
- [Environment Variables](#environment-variables)
- [Monitoring](#monitoring)
- [Troubleshooting](#troubleshooting)

---

## ✅ Prerequisites

### Hardware Requirements

**Minimum:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB SSD
- Network: 100 Mbps

**Recommended (with Ollama):**
- CPU: 8+ cores
- RAM: 16GB+
- Storage: 100GB+ SSD
- GPU: 8GB+ VRAM (optional, for faster inference)

### Software Requirements

```bash
# Operating System
Ubuntu 22.04 LTS or later

# Python
Python 3.11+

# Node.js
Node.js 20.9.0+
npm 10+

# Database
SQLite (included) or PostgreSQL (optional)

# Ollama (optional, for local models)
Ollama 0.1.0+
```

---

## 🖥️ Server Setup

### 1. Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install Dependencies

```bash
# Python & pip
sudo apt install python3.11 python3.11-venv python3-pip -y

# Node.js & npm
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install nodejs -y

# Git
sudo apt install git -y

# Build tools
sudo apt install build-essential -y
```

### 3. Install Ollama (Optional)

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
sudo systemctl start ollama
sudo systemctl enable ollama

# Pull models
ollama pull mistral:latest
ollama pull llama3.1:latest
ollama pull deepseek-coder:latest
ollama pull mixtral:latest
```

### 4. Create Application User

```bash
# Create user
sudo useradd -m -s /bin/bash agent

# Set password (optional)
sudo passwd agent

# Add to sudo group (if needed)
sudo usermod -aG sudo agent
```

---

## 🔧 Backend Deployment

### 1. Clone Repository

```bash
# Create the production directory and set ownership
sudo mkdir -p /srv/ai_agent
sudo chown agent:agent /srv/ai_agent

# Switch to agent user
sudo su - agent

# Clone repo directly into /srv/ai_agent
git clone https://github.com/pandenis/ai_agent_v2.git /srv/ai_agent
cd /srv/ai_agent

# Or pull if already exists
git pull
```

### 2. Create Virtual Environment

```bash
# Create venv
python3.11 -m venv venv

# Activate
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip
```

### 3. Install Dependencies

```bash
# Install requirements
pip install -r requirements.txt

# For production, also install gunicorn
pip install gunicorn uvicorn[standard]
```

### 4. Configure Environment

```bash
# Create .env file
cat > .env << 'EOF'
# Application
APP_NAME="AI Agent System"
DEBUG=false
LOG_LEVEL=INFO
ENVIRONMENT=production

# Database
DATABASE_URL=sqlite+aiosqlite:///./data/agent.db

# Ollama (local models)
OLLAMA_HOST=http://localhost:11434

# Groq (cloud API)
GROQ_API_KEY=your_groq_api_key_here
GROQ_API_BASE=https://api.groq.com/openai/v1

# Memorisator
memorisator_enabled=true
max_memory_facts=10000
fact_importance_threshold=0.5
fact_confidence_threshold=0.7

# Security
SECRET_KEY=$(openssl rand -hex 32)
ALLOWED_ORIGINS=http://localhost:3000,http://192.168.1.237:3000

# Performance
MAX_WORKERS=4
TIMEOUT=300
EOF

# Secure the file
chmod 600 .env
```

### 5. Initialize Database

```bash
# Create data directory
mkdir -p data

# Run migrations (if any)
# python app/db/migrate.py

# Database is created automatically on first run
```

### 6. Test Backend

```bash
# Test run
uvicorn app.main:app --host 0.0.0.0 --port 8000

# In another terminal, test
curl http://localhost:8000/api/v1/health

# Should return: {"status": "healthy"}
```

---

## 🎨 Frontend Deployment

### 1. Navigate to Frontend

```bash
cd /srv/ai_agent/ui/ai-agent-ui
```

### 2. Install Dependencies

```bash
npm install
```

### 3. Configure Environment

```bash
# Create .env.local
cat > .env.local << 'EOF'
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
EOF
```

### 4. Build Frontend

```bash
# Production build
npm run build

# This creates .next/ directory
```

### 5. Test Frontend

```bash
# Test production build
npm start

# Visit http://localhost:3000
# Verify the UI loads correctly, then STOP the server:
# Press Ctrl+C to stop npm start before proceeding
```

> ⚠️ **Important:** Stop the test server (Ctrl+C) before continuing.
> The systemd service will also run on port 3000 — if the manual server
> is still running, the service will fail with `EADDRINUSE :::3000`.

---

## ⚙️ Systemd Services

### Backend Service

```bash
# Create service file
sudo nano /etc/systemd/system/ai-agent.service
```

**Content:**
```ini
[Unit]
Description=AI Agent Backend Service
After=network.target

[Service]
Type=simple
User=agent
WorkingDirectory=/srv/ai_agent
Environment="PATH=/srv/ai_agent/venv/bin"
ExecStart=/srv/ai_agent/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

> **Note:** Development environment uses `/srv/ai_agent_dev_git`
> on port 8001 with service name `ai-agent-dev.service`.
> Production always runs from `/srv/ai_agent` on port 8000.

**Enable & Start:**
```bash
sudo systemctl daemon-reload
sudo systemctl enable ai-agent.service
sudo systemctl start ai-agent.service
sudo systemctl status ai-agent.service
```

---

### Frontend Service

```bash
# Create service file
sudo nano /etc/systemd/system/ai-agent-ui.service
```

**Content:**
```ini
[Unit]
Description=AI Agent Frontend Service
After=network.target

[Service]
Type=simple
User=agent
WorkingDirectory=/srv/ai_agent/ui/ai-agent-ui
Environment="PATH=/usr/bin:/usr/local/bin"
Environment="NODE_ENV=production"
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Enable & Start:**
```bash
# Ensure no manual npm start is running on port 3000:
lsof -ti:3000 | xargs kill -9 2>/dev/null || true

sudo systemctl daemon-reload
sudo systemctl enable ai-agent-ui.service
sudo systemctl start ai-agent-ui.service
sudo systemctl status ai-agent-ui.service
```

---

## 🌐 Nginx Configuration (Optional)

### Install Nginx

```bash
sudo apt install nginx -y
```

### Configure Reverse Proxy

```bash
sudo nano /etc/nginx/sites-available/ai-agent
```

**Content:**
```nginx
server {
    listen 80;
    server_name your-domain.com;  # or IP address

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://localhost:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeout for long-running requests
        proxy_read_timeout 300s;
        proxy_connect_timeout 300s;
    }
}
```

**Enable Site:**
```bash
sudo ln -s /etc/nginx/sites-available/ai-agent /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 🔐 SSL/TLS with Let's Encrypt (Optional)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

---

## 📊 Environment Variables Reference

### Backend (.env)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `APP_NAME` | Application name | "AI Agent System" | No |
| `DEBUG` | Debug mode | false | No |
| `LOG_LEVEL` | Logging level | INFO | No |
| `DATABASE_URL` | Database connection | sqlite://... | Yes |
| `OLLAMA_HOST` | Ollama API URL | http://localhost:11434 | No |
| `GROQ_API_KEY` | Groq API key | - | Yes* |
| `memorisator_enabled` | Enable fact extraction | true | No |
| `max_memory_facts` | Max facts to store | 10000 | No |
| `SECRET_KEY` | Security secret | - | Yes |
| `ALLOWED_ORIGINS` | CORS origins | localhost | No |

\* Required if using Groq agent

### Frontend (.env.local)

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `NEXT_PUBLIC_API_URL` | Backend API URL | http://localhost:8000/api/v1 | Yes |

---

## 📈 Monitoring

### Check Service Status

```bash
# Backend
sudo systemctl status ai-agent.service

# Frontend
sudo systemctl status ai-agent-ui.service

# Logs
sudo journalctl -u ai-agent.service -f
sudo journalctl -u ai-agent-ui.service -f
```

### Check Application Health

```bash
# Health endpoint
curl http://localhost:8000/api/v1/health

# Check Ollama
curl http://localhost:11434/api/tags
```

### Resource Monitoring

```bash
# CPU & Memory
htop

# Disk usage
df -h

# Network
netstat -tulpn | grep LISTEN
```

---

## 🔧 Troubleshooting

### Backend Issues

**Problem:** Backend won't start
```bash
# Check logs
sudo journalctl -u ai-agent.service -n 50

# Common issues:
# 1. Python venv not activated - check ExecStart path
# 2. Port 8000 in use - change port or kill process
# 3. Database permissions - check data/ directory ownership
```

**Problem:** Ollama models not found
```bash
# Check Ollama is running
sudo systemctl status ollama

# List available models
ollama list

# Pull missing model
ollama pull mistral:latest
```

**Problem:** High memory usage
```bash
# Reduce Ollama concurrent requests
# Edit OLLAMA_MAX_LOADED_MODELS in ollama config

# Reduce uvicorn workers
# Edit --workers parameter in systemd service
```

---

### Frontend Issues

**Problem:** Frontend won't build
```bash
# Clear cache
rm -rf .next node_modules
npm install
npm run build
```

**Problem:** API connection fails
```bash
# Check NEXT_PUBLIC_API_URL in .env.local
# Check CORS settings in backend .env
# Check backend is running: curl http://localhost:8000/api/v1/health
```

**Problem:** "Module not found" errors
```bash
# Reinstall dependencies
rm -rf node_modules package-lock.json
npm install
```

---

### Database Issues

**Problem:** Database locked
```bash
# SQLite is single-writer
# Check no other processes accessing database
lsof | grep agent.db

# Consider upgrading to PostgreSQL for production
```

**Problem:** Migration needed
```bash
# Backup first
cp data/agent.db data/agent.db.backup

# Run migrations (if you have migration scripts)
# python app/db/migrate.py
```

---

## 🔄 Updates & Maintenance

### Updating the Application

```bash
# As agent user
cd /srv/ai_agent

# Backup database
cp data/agent.db data/agent.db.backup.$(date +%Y%m%d)

# Pull latest code
git pull

# Update backend dependencies
source venv/bin/activate
pip install -r requirements.txt --upgrade

# Update frontend dependencies
cd ui/ai-agent-ui
npm install

# Rebuild frontend
npm run build

# Restart services
sudo systemctl restart ai-agent.service
sudo systemctl restart ai-agent-ui.service

# Check health
curl http://localhost:8000/api/v1/health
```

### Backup Strategy

```bash
# Create backup script
cat > /srv/ai_agent/scripts/backup.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/srv/ai_agent/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup database
cp /srv/ai_agent/data/agent.db $BACKUP_DIR/agent.db.$DATE

# Backup .env
cp /srv/ai_agent/.env $BACKUP_DIR/.env.$DATE

# Keep only last 7 days
find $BACKUP_DIR -name "agent.db.*" -mtime +7 -delete

echo "Backup completed: $DATE"
EOF

chmod +x /srv/ai_agent/scripts/backup.sh

# Add to crontab (daily at 2 AM)
crontab -e
# Add: 0 2 * * * /srv/ai_agent/scripts/backup.sh
```

---

## 🎯 Production Checklist

Before going live:

```
✅ Environment variables configured
✅ Database initialized
✅ Ollama models pulled
✅ Systemd services created and enabled
✅ Services running without errors
✅ Health check returns "healthy"
✅ Frontend accessible
✅ API endpoints working
✅ Backups configured
✅ Monitoring set up
✅ Firewall configured (if needed)
✅ SSL certificate installed (if public)
✅ CORS configured correctly
✅ Logs rotating properly
```

---

## 📞 Support

If you encounter issues:

1. Check logs: `sudo journalctl -u ai-agent.service -f`
2. Check health: `curl http://localhost:8000/api/v1/health`
3. Review this guide
4. Check GitHub issues
5. Create new issue with logs

---

**Last Updated:** December 9, 2025  
**Deployment Version:** Production v2.0  
**Tested On:** Ubuntu 22.04 LTS