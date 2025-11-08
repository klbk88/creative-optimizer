# 🚂 Railway Deployment Guide

Quick guide to deploy Creative Optimizer to Railway.

## 📋 Prerequisites

1. **Railway Account**: Sign up at https://railway.app
2. **GitHub repo**: Code already pushed to https://github.com/klbk88/creative-optimizer

## 🚀 Quick Deploy (5 minutes)

### Step 1: Create New Project on Railway

```bash
# Option A: Railway CLI (recommended)
npm install -g @railway/cli
railway login
railway init

# Option B: Web UI
# Go to https://railway.app/new
# Click "Deploy from GitHub repo"
# Select: klbk88/creative-optimizer
```

### Step 2: Add PostgreSQL Database

```
Railway Dashboard → New → Database → PostgreSQL
```

Railway will automatically create `DATABASE_URL` environment variable.

### Step 3: Add Redis

```
Railway Dashboard → New → Database → Redis
```

Railway will automatically create `REDIS_URL` environment variable.

### Step 4: Configure Environment Variables

Go to your service → Variables → Add the following:

```bash
# Required
JWT_SECRET_KEY=your-super-secret-key-change-this
ANTHROPIC_API_KEY=sk-ant-xxx  # Optional - for AI creative analysis

# Optional - Bot
ADMIN_BOT_TOKEN=your_telegram_bot_token
TG_BOT_TOKEN=your_telegram_bot_token

# Optional - Landing pages
LANDING_BASE_URL=https://your-app.railway.app/api/v1/landing/l
TELEGRAM_BOT_USERNAME=your_bot_username

# Product theme
PRODUCT_THEME=white
ATTRIBUTION_WINDOW_HOURS=72
ML_RETRAIN_INTERVAL_DAYS=4
USE_PUBLIC_DATA_BOOTSTRAP=true

# Storage (optional - defaults to local)
STORAGE_TYPE=local
```

### Step 5: Deploy!

Railway will automatically deploy when you push to GitHub.

```bash
# Or deploy manually:
railway up
```

## 🔧 Project Structure on Railway

You'll have 3 services:

```
1. creative-optimizer-api (FastAPI)
   - Port: $PORT (auto-assigned by Railway)
   - Start: uvicorn api.main:app --host 0.0.0.0 --port $PORT

2. postgres (Database)
   - Auto-managed by Railway
   - DATABASE_URL auto-injected

3. redis (Cache)
   - Auto-managed by Railway
   - REDIS_URL auto-injected
```

**Optional:** Add admin bot as separate service
```
4. admin-bot (Telegram Bot)
   - Start: python bots/admin_bot.py
```

## 📊 Database Migration

Railway will automatically run migrations on deploy. To run manually:

```bash
# Via Railway CLI
railway run alembic upgrade head

# Or add to Dockerfile (already configured)
```

## 🌐 Access Your App

After deployment:
- **API**: `https://your-app.railway.app`
- **Docs**: `https://your-app.railway.app/docs`
- **Health**: `https://your-app.railway.app/health`

## 💰 Cost Estimation

**Hobby Plan ($5/month):**
- FastAPI app: ~$3/month (500 hours included)
- PostgreSQL: Included
- Redis: Included
- Total: **$5/month**

**Pro Plan ($20/month):**
- Unlimited execution time
- Better performance
- More resources

## 🐛 Troubleshooting

### Build fails with OpenCV/librosa errors

Railway should install all system dependencies from Dockerfile. If it fails:

```dockerfile
# Dockerfile already has these, but verify:
RUN apt-get install -y \
    libsndfile1 \        # For librosa
    libgl1-mesa-glx \    # For OpenCV
    libglib2.0-0 \       # For OpenCV
    ffmpeg               # For video processing
```

### Database connection fails

Check that `DATABASE_URL` is injected:
```bash
railway variables
```

Should show: `DATABASE_URL=postgresql://...`

### Port binding error

Railway sets `$PORT` automatically. Make sure Dockerfile uses it:
```dockerfile
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT}
```

## 📱 Deploy Admin Bot Separately

The admin bot should run as a separate service:

```bash
# In Railway:
# New Service → From GitHub → Same repo
# Override start command:
python bots/admin_bot.py
```

Environment variables needed:
```
ADMIN_BOT_TOKEN=xxx
TRACKING_API_URL=https://your-api.railway.app
ADMIN_JWT_TOKEN=xxx (get from /api/v1/auth/login)
```

## 🔄 Auto-Deploy on Git Push

Railway automatically deploys when you push to `main`:

```bash
git add .
git commit -m "Update feature"
git push origin main
# → Railway auto-deploys!
```

## 📈 Monitoring

Railway provides:
- **Logs**: Real-time in dashboard
- **Metrics**: CPU, Memory, Network
- **Deployments**: History & rollback

Access at: `https://railway.app/project/your-project/metrics`

## 🎯 Next Steps

1. ✅ Deploy API to Railway
2. ✅ Test `/docs` endpoint
3. ✅ Create admin user via `/api/v1/auth/register`
4. ✅ Get JWT token
5. ✅ Deploy admin bot (optional)
6. ✅ Test creative analysis workflow

## 🆘 Need Help?

- Railway Docs: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- This project: https://github.com/klbk88/creative-optimizer/issues

---

**Ready to deploy? Let's go! 🚀**
