# 🐳 PayShield AI — Docker Setup Guide

## Overview

PayShield AI runs as a single-host Docker Compose stack. All services — frontend, backend, and database — run on one Alibaba Cloud ECS instance.

```
┌─────────────────────────────────────────┐
│         Alibaba Cloud ECS Instance      │
│                                         │
│  ┌───────────────┐  ┌────────────────┐  │
│  │    frontend   │  │    backend     │  │
│  │  (Nginx +     │  │  (FastAPI      │  │
│  │   React SPA)  │  │   Uvicorn)     │  │
│  │   Port 80     │  │   Port 8000    │  │
│  └───────────────┘  └───────┬────────┘  │
│                             │           │
│               ┌─────────────▼──────┐    │
│               │   db (PostgreSQL)  │    │
│               │   Port 5432        │    │
│               └────────────────────┘    │
└─────────────────────────────────────────┘
```

**Default (dev):** Backend uses SQLite file — no `db` service needed.  
**Production:** Switch `DATABASE_URL` to PostgreSQL and enable the `db` service.

---

## Table of Contents
1. [File Structure](#1-file-structure)
2. [docker-compose.yml](#2-docker-composeyml)
3. [Backend Dockerfile](#3-backend-dockerfile)
4. [Frontend Dockerfile](#4-frontend-dockerfile)
5. [Nginx Config](#5-nginx-config)
6. [Environment File](#6-environment-file)
7. [Common Commands](#7-common-commands)
8. [Alibaba ECS Deployment](#8-alibaba-ecs-deployment)

---

## 1. File Structure

```
payshield-ai/
├── docker-compose.yml
├── docker-compose.prod.yml      ← Override for PostgreSQL production
├── .env.example
├── .env                         ← Your secrets (never commit)
├── backend/
│   └── Dockerfile
└── frontend/
    ├── Dockerfile
    └── nginx.conf
```

---

## 2. docker-compose.yml

**`docker-compose.yml`** (development — SQLite):

```yaml
version: "3.9"

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: payshield-backend
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL:-sqlite:///./payshield.db}
      - QWEN_API_KEY=${QWEN_API_KEY}
      - QWEN_MODEL=${QWEN_MODEL:-qwen-max}
      - QWEN_BASE_URL=${QWEN_BASE_URL:-https://dashscope.aliyuncs.com/compatible-mode/v1}
      - FRONTEND_URL=${FRONTEND_URL:-http://localhost:5173}
      - SECRET_KEY=${SECRET_KEY:-dev-secret-key-change-in-prod}
      - ENVIRONMENT=${ENVIRONMENT:-development}
      - ENABLE_FACE_MATCH=${ENABLE_FACE_MATCH:-true}
      - ENABLE_ENTITY_SCRAPE=${ENABLE_ENTITY_SCRAPE:-false}
    volumes:
      - sqlite-data:/app/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        - VITE_API_URL=${VITE_API_URL:-http://localhost:8000}
    container_name: payshield-frontend
    ports:
      - "80:80"
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  sqlite-data:
```

**`docker-compose.prod.yml`** (override for PostgreSQL):

```yaml
version: "3.9"

services:
  db:
    image: postgres:16-alpine
    container_name: payshield-db
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-payshield}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB:-payshield}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U payshield"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-payshield}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB:-payshield}
    depends_on:
      db:
        condition: service_healthy

volumes:
  postgres-data:
```

**Run with PostgreSQL:**
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build
```

---

## 3. Backend Dockerfile

**`backend/Dockerfile`**:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system deps
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create data directory for SQLite
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

---

## 4. Frontend Dockerfile

**`frontend/Dockerfile`**:

```dockerfile
# Stage 1: Build React app
FROM node:20-alpine AS builder

WORKDIR /app

# Accept build arg for API URL
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

# Install dependencies
COPY package*.json ./
RUN npm ci

# Copy source and build
COPY . .
RUN npm run build

# Stage 2: Serve with Nginx
FROM nginx:alpine

# Copy built assets
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy Nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

---

## 5. Nginx Config

**`frontend/nginx.conf`**:

```nginx
server {
    listen 80;
    server_name _;
    root /usr/share/nginx/html;
    index index.html;

    # React SPA: serve index.html for all non-asset routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy /api requests to FastAPI backend
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN";
    add_header X-Content-Type-Options "nosniff";
    add_header Referrer-Policy "strict-origin-when-cross-origin";
}
```

---

## 6. Environment File

**`.env.example`** (copy to `.env` and fill in values):

```env
# ── Qwen / Alibaba Model Studio ──────────────────────────────────────
QWEN_API_KEY=sk-your-alibaba-model-studio-api-key-here
QWEN_MODEL=qwen-max
QWEN_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1

# ── Backend ───────────────────────────────────────────────────────────
# SQLite (default for dev):
DATABASE_URL=sqlite:///./data/payshield.db
# PostgreSQL (for prod, use docker-compose.prod.yml):
# DATABASE_URL=postgresql://payshield:your_password@db:5432/payshield

SECRET_KEY=replace-with-a-long-random-string-for-production
ENVIRONMENT=development

# ── CORS ──────────────────────────────────────────────────────────────
FRONTEND_URL=http://localhost:80

# ── Feature Flags ────────────────────────────────────────────────────
ENABLE_FACE_MATCH=true
ENABLE_ENTITY_SCRAPE=false

# ── Frontend Build Arg ────────────────────────────────────────────────
# When using Nginx proxy (Docker), leave empty (proxy handles /api)
VITE_API_URL=

# ── PostgreSQL (only if using docker-compose.prod.yml) ────────────────
POSTGRES_USER=payshield
POSTGRES_PASSWORD=your_secure_postgres_password
POSTGRES_DB=payshield
```

---

## 7. Common Commands

### Start (development, SQLite)
```bash
docker-compose up --build
```

### Start (production, PostgreSQL)
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

### Stop all services
```bash
docker-compose down
```

### Stop and remove volumes (⚠️ deletes database)
```bash
docker-compose down -v
```

### View logs
```bash
# All services
docker-compose logs -f

# Backend only
docker-compose logs -f backend

# Frontend only
docker-compose logs -f frontend
```

### Rebuild a single service
```bash
docker-compose up --build backend
```

### Seed demo data
```bash
docker-compose exec backend python seed_demo.py
```

### Open shell in backend container
```bash
docker-compose exec backend bash
```

### Check backend health
```bash
curl http://localhost:8000/health
```

---

## 8. Alibaba ECS Deployment

### Step 1: Create ECS Instance

1. Log into Alibaba Cloud Console
2. Go to **ECS** → **Instances** → **Create Instance**
3. Recommended spec for hackathon: **2 vCPU, 4GB RAM** (ecs.c7.large)
4. OS: **Ubuntu 22.04 LTS**
5. Security Group: Open ports **80** (HTTP) and **22** (SSH)
6. Assign **Elastic IP (EIP)** for public access

### Step 2: Install Docker on ECS

```bash
# SSH into instance
ssh root@<your-ecs-ip>

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose plugin
apt-get install -y docker-compose-plugin

# Verify
docker --version
docker compose version
```

### Step 3: Clone and Configure

```bash
git clone https://github.com/JarjitGASS/Payshield-AI.git
cd Payshield-AI
cp .env.example .env
nano .env   # Fill in QWEN_API_KEY and other values
```

### Step 4: Start Services

```bash
docker compose up --build -d
```

### Step 5: Seed Demo Data

```bash
docker compose exec backend python seed_demo.py
```

### Step 6: Verify

```bash
# Check all services are running
docker compose ps

# Check backend health
curl http://localhost:8000/health

# Access from public internet
# Frontend: http://<your-ecs-ip>
# API Docs: http://<your-ecs-ip>/api/docs  (via Nginx proxy)
```

### Cost Estimate

| Resource | Cost (48hr) |
|---|---|
| ECS ecs.c7.large (2C4G) | ~$2.50 |
| Qwen API calls (est. 200 assessments) | ~$3–6 |
| Elastic IP | ~$0.10 |
| **Total estimate** | **< $10** |

> **Tip:** Use `qwen-turbo` during development/testing and switch to `qwen-max` for the demo to save credits.

### Alibaba Model Studio API Key Setup

1. Go to [Alibaba Cloud Model Studio](https://modelstudio.console.aliyun.com/)
2. Create a new API key
3. Copy the key to your `.env` file as `QWEN_API_KEY`
4. The base URL for OpenAI-compatible mode is: `https://dashscope.aliyuncs.com/compatible-mode/v1`
