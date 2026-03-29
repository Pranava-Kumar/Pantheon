# Free Tier Deployment Guide 🆓

Deploy Project Pantheon to production using 100% free services.

---

## 🎯 Deployment Options

### Option 1: Docker Compose (Self-Hosted) - RECOMMENDED

**Best for:** Full control, no usage limits

**Requirements:**
- Server with 4GB+ RAM (Oracle Cloud Free Tier, etc.)
- Docker & Docker Compose installed

**Steps:**

```bash
# 1. Clone repository
git clone https://github.com/Pranava-Kumar/Pantheon.git
cd Pantheon

# 2. Create .env file
cp .env.example .env
# Edit .env with your API keys

# 3. Start all services
docker-compose up -d

# 4. Check logs
docker-compose logs -f

# 5. Access services
# API: http://your-server-ip:8000/docs
# Dashboard: http://your-server-ip:8501
```

**Free Server Options:**
- **Oracle Cloud Free Tier:** 4 OCPU, 24GB RAM (always free)
- **Google Cloud Free Tier:** e2-micro (0.25 vCPU, 1GB RAM)
- **AWS Free Tier:** t2.micro (1 vCPU, 1GB RAM, 12 months)

---

### Option 2: Render.com (Easiest)

**Best for:** Quick deployment, no server management

**Free Tier Limits:**
- 750 hours/month (enough for 1 service)
- 512MB RAM
- Auto-sleep after 15 min inactivity

**Steps:**

1. **Push to GitHub**
   ```bash
   git push origin main
   ```

2. **Deploy to Render:**
   - Go to https://render.com
   - Sign up with GitHub
   - Click "New +" → "Web Service"
   - Connect your repository
   - Configure:
     - **Name:** pantheon-api
     - **Environment:** Python 3.11
     - **Build Command:** `pip install -r requirements.txt`
     - **Start Command:** `uvicorn pantheon.api.main:app --host 0.0.0.0 --port $PORT`
     - **Instance Type:** Free

3. **Add Environment Variables:**
   - Copy all values from `.env.example` to Render environment variables
   - Use Neon for database (see below)

4. **Deploy Dashboard (separate service):**
   - New "Web Service"
   - **Start Command:** `streamlit run pantheon/dashboard/app.py --server.address=0.0.0.0 --server.port=$PORT`

---

### Option 3: Railway.app

**Best for:** More generous free tier ($5 credit/month)

**Steps:**

1. **Sign up:** https://railway.app
2. **New Project** → "Deploy from GitHub repo"
3. **Select repository:** Pantheon
4. **Add variables** from `.env.example`
5. **Deploy**

Railway automatically detects `requirements.txt` and creates appropriate build commands.

---

## 🗄️ Database Setup (Free)

### Neon PostgreSQL (Recommended)

**Free Tier:** 0.5 GB storage, unlimited databases

**Setup:**
1. Go to https://neon.tech
2. Sign up with GitHub
3. Create new project: "pantheon"
4. Copy connection string
5. Update `.env`:
   ```env
   DATABASE_URL=postgresql://user:pass@ep-xxx.us-east-2.aws.neon.tech/pantheon
   DATABASE_URL_ASYNC=postgresql+asyncpg://user:pass@ep-xxx.us-east-2.aws.neon.tech/pantheon
   ```

### SQLite (Simplest)

**Free Tier:** Unlimited (file-based)

**Setup:**
```env
DATABASE_URL=sqlite:///./pantheon.db
DATABASE_URL_ASYNC=sqlite+aiosqlite:///./pantheon.db
```

No setup required! Database file is created automatically.

---

## 🔴 Redis Setup (Free)

### Redis Cloud

**Free Tier:** 30MB, 1 connection

**Setup:**
1. Go to https://redis.com/try-free/
2. Sign up
3. Create free database
4. Copy "Public endpoint" URL
5. Update `.env`:
   ```env
   REDIS_URL=redis://redis-xxx.us-east-1-2.ec2.redns.redis-cloud.com:xxxx
   ```

### Self-Hosted (Docker)

If using Docker Compose, Redis is included in `docker-compose.yml`.

---

## 🔑 API Keys (All Free)

### LLM APIs

| Service | Free Tier | Sign Up |
|---------|-----------|---------|
| **Google Gemini** | 60 requests/min | [Get Key](https://makersuite.google.com/app/apikey) |
| **Groq** | 30 requests/min | [Get Key](https://console.groq.com/keys) |
| **HuggingFace** | 30 requests/hour | [Get Key](https://huggingface.co/settings/tokens) |

### Market Data

| Service | Free Tier | Sign Up |
|---------|-----------|---------|
| **Upstox** | Free market data | [Get Key](https://upstox.com/developer/) |
| **Screener.in** | Free fundamental data | [Sign Up](https://www.screener.in) |

---

## 📊 Monitoring (Free)

### Health Check Endpoint

```bash
curl http://your-server:8000/api/v1/health
```

Response:
```json
{
  "status": "ok",
  "database": "connected",
  "redis": "connected",
  "timestamp": "2026-03-28T12:00:00Z",
  "total_signals": 127,
  "total_trades": 45
}
```

### Uptime Monitoring

Use free services:
- **UptimeRobot:** https://uptimerobot.com (50 monitors, 5 min intervals)
- **PingPing:** https://pingping.eu (10 monitors, 1 min intervals)

Configure to monitor: `http://your-server:8000/api/v1/health`

---

## 🚀 Deployment Checklist

### Pre-Deployment
- [ ] All API keys obtained (Gemini, Groq, Upstox, Screener)
- [ ] Database configured (Neon or SQLite)
- [ ] Redis configured (Redis Cloud or Docker)
- [ ] JWT secret generated: `python -c "import secrets; print(secrets.token_hex(32))"`
- [ ] `.env` file created with all values

### Post-Deployment
- [ ] Health check returns 200 OK
- [ ] Database tables created (check logs)
- [ ] Redis connected (check health endpoint)
- [ ] API docs accessible: `/docs`
- [ ] Dashboard accessible: `:8501`
- [ ] Daily analysis scheduled (check GitHub Actions)

---

## 🔧 Troubleshooting

### Issue: "Module not found"

**Solution:**
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Issue: "Database not connected"

**Solution:**
1. Check DATABASE_URL in `.env`
2. For Neon: Verify connection string includes SSL mode
3. Check logs: `docker-compose logs api`

### Issue: "Redis connection refused"

**Solution:**
1. Check REDIS_URL in `.env`
2. For Redis Cloud: Whitelist your server IP
3. For Docker: Ensure Redis service is running

### Issue: "Rate limit exceeded"

**Solution:**
1. Check API key quotas (Gemini: 60/min, Groq: 30/min)
2. Reduce watchlist size if needed
3. Add more free API keys (multiple HuggingFace accounts)

---

## 📈 Scaling (Still Free)

### Multiple API Keys

Rotate between multiple free API keys:

```python
# pantheon/extractors/__init__.py
GEMINI_KEYS = [
    os.getenv("GOOGLE_API_KEY_1"),
    os.getenv("GOOGLE_API_KEY_2"),
    # Add more keys
]
```

### Horizontal Scaling

Deploy multiple API instances behind a load balancer:

```yaml
# docker-compose.yml
api:
  deploy:
    replicas: 3
```

### Database Optimization

Add indexes for faster queries:

```sql
CREATE INDEX idx_signal_timestamp ON signals(timestamp);
CREATE INDEX idx_signal_symbol ON signals(symbol);
```

---

## 💰 Cost Breakdown

| Service | Free Tier | Cost |
|---------|-----------|------|
| **Hosting** | Oracle Cloud / Render | $0 |
| **Database** | Neon (0.5GB) | $0 |
| **Redis** | Redis Cloud (30MB) | $0 |
| **LLM APIs** | Gemini + Groq + HF | $0 |
| **Market Data** | Upstox + Screener | $0 |
| **Monitoring** | UptimeRobot | $0 |
| **Total** | | **$0/month** |

---

## 🎉 Success!

Your Project Pantheon is now deployed and running on 100% free infrastructure!

**Next Steps:**
1. Monitor health endpoint daily
2. Check dashboard for signals
3. Review paper trading performance
4. Adjust model weights based on performance

**Support:**
- Issues: https://github.com/Pranava-Kumar/Pantheon/issues
- Discussions: https://github.com/Pranava-Kumar/Pantheon/discussions

---

**Built with ❤️ using 100% free and open-source tools**
