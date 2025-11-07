# Railway Deployment Guide for Dog Food API

This guide will help you deploy your FastAPI application with Celery background workers on Railway.

## Prerequisites

1. **Railway Account**: Sign up at [railway.app](https://railway.app)
2. **GitHub Repository**: Your code should be pushed to GitHub
3. **Railway CLI** (optional): Install with `npm install -g @railway/cli`

## Step 1: Prepare Your Repository

### 1.1 Create Railway Configuration Files

Create `railway.json` in your project root:

```json
{
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

### 1.2 Update Dockerfile for Railway

Your existing Dockerfile is good and already has a health check. The health endpoint at `/health` is already implemented in your `app/main.py`.

### 1.3 Create Railway Service Files

Create separate service files for different components:

**`railway-web.json`** (for the main API):
```json
{
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "healthcheckTimeout": 100,
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

**`railway-worker.json`** (for Celery worker):
```json
{
  "deploy": {
    "startCommand": "celery -A app.tasks.scraping_tasks worker --loglevel=info",
    "restartPolicyType": "ON_FAILURE",
    "restartPolicyMaxRetries": 10
  }
}
```

## Step 2: Deploy on Railway

### 2.1 Create New Project

1. Go to [railway.app](https://railway.app)
2. Click "New Project"
3. Select "GitHub Repository"
4. Choose your dog-food-audition-api repository
5. Railway will automatically detect it's a Python project

### 2.2 Add Database Service

1. In your Railway project dashboard, click "+ New"
2. Select "Database" → "PostgreSQL"
3. Railway will create a PostgreSQL database
4. Note the connection details (you'll need them for environment variables)

### 2.3 Add Redis Service

1. Click "+ New" again
2. Select "Database" → "Redis"
3. Railway will create a Redis instance
4. Note the connection details

### 2.4 Configure Main Web Service

1. Railway should have automatically created a service from your GitHub repo
2. Click on the service to configure it
3. Go to "Settings" → "Environment"
4. Add these environment variables:

```bash
# Database
DATABASE_URL=postgresql://postgres:password@host:port/database
DATABASE_URL_ASYNC=postgresql+asyncpg://postgres:password@host:port/database

# Redis
REDIS_URL=redis://username:password@host:port

# App Configuration
SECRET_KEY=your-super-secret-key-here
DEBUG=False
LOG_LEVEL=INFO
LOG_FORMAT=json

# Celery (disable scheduling by default)
ENABLE_CELERY_BEAT=false
```

### 2.5 Create Celery Worker Service

1. Click "+ New" → "GitHub Repo"
2. Select the same repository
3. In the service settings:
   - **Name**: `dog-food-worker`
   - **Start Command**: `celery -A app.tasks.scraping_tasks worker --loglevel=info`
4. Add the same environment variables as the web service

### 2.6 Optional: Create Celery Beat Service (for scheduling)

If you want periodic scraping (not recommended for now):

1. Click "+ New" → "GitHub Repo"
2. Select the same repository
3. In the service settings:
   - **Name**: `dog-food-beat`
   - **Start Command**: `celery -A app.tasks.scraping_tasks beat --loglevel=info`
4. Add the same environment variables PLUS:
   - `ENABLE_CELERY_BEAT=true`

## Step 3: Environment Variables Setup

### 3.1 Get Database Connection String

1. Go to your PostgreSQL service in Railway
2. Click on "Connect"
3. Copy the connection string
4. Use it for `DATABASE_URL` and `DATABASE_URL_ASYNC`

### 3.2 Get Redis Connection String

1. Go to your Redis service in Railway
2. Click on "Connect"
3. Copy the connection string
4. Use it for `REDIS_URL`

### 3.3 Generate Secret Key

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

## Step 4: Database Migration

### 4.1 Run Migrations

You'll need to run database migrations. You can do this by:

1. **Option A**: Add a migration service
   - Create a new service with start command: `alembic upgrade head`
   - Run it once, then delete the service

2. **Option B**: SSH into your web service and run migrations
   - Use Railway CLI: `railway run alembic upgrade head`

### 4.2 Create Migration Service (Recommended)

1. Create a new service called `migration`
2. Start command: `alembic upgrade head`
3. Run it once, then you can delete it

## Step 5: Testing Your Deployment

### 5.1 Check Services

1. **Web Service**: Should be accessible at the provided Railway URL
2. **Worker Service**: Check logs to ensure Celery worker is running
3. **Database**: Check connection in web service logs

### 5.2 Test API Endpoints

```bash
# Health check
curl https://your-app.railway.app/health

# Test scraping (requires authentication)
curl -X POST https://your-app.railway.app/api/v1/scraping/run \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 5.3 Monitor Logs

1. Go to each service in Railway dashboard
2. Click "Logs" tab
3. You should see:
   - Web service: FastAPI startup logs
   - Worker service: Celery worker startup logs
   - Structured logs with task IDs when running scraping

## Step 6: Production Considerations

### 6.1 Security

1. **Change default secret key**
2. **Configure CORS properly** (update `allow_origins` in `main.py`)
3. **Set up proper authentication**
4. **Use HTTPS** (Railway provides this automatically)

### 6.2 Monitoring

1. **Railway provides built-in monitoring**
2. **Check service health in dashboard**
3. **Monitor resource usage**

### 6.3 Scaling

1. **Railway auto-scales based on traffic**
2. **You can manually scale services in dashboard**
3. **Monitor costs in Railway billing**

## Step 7: Troubleshooting

### 7.1 Common Issues

**Service won't start:**
- Check environment variables
- Check start command
- Check logs for errors

**Database connection issues:**
- Verify `DATABASE_URL` format
- Check if database service is running
- Run migrations

**Celery worker issues:**
- Check `REDIS_URL` is correct
- Verify Redis service is running
- Check worker logs

**API not accessible:**
- Check if web service is running
- Verify port configuration
- Check Railway URL

### 7.2 Debug Commands

```bash
# Check service status
railway status

# View logs
railway logs

# Connect to service
railway connect

# Run commands in service
railway run python -c "import app.core.config; print(app.core.config.get_settings())"
```

## Step 8: Cost Management

### 8.1 Railway Pricing

- **Free tier**: Limited resources
- **Pro plan**: $5/month per service
- **Database**: Additional cost for PostgreSQL/Redis

### 8.2 Optimize Costs

1. **Use only necessary services** (skip beat service for now)
2. **Monitor resource usage**
3. **Scale down when not needed**

## Step 9: Final Checklist

- [ ] Web service running and accessible
- [ ] Database connected and migrated
- [ ] Redis connected
- [ ] Celery worker running
- [ ] API endpoints responding
- [ ] Scraping task can be triggered via API
- [ ] Task status can be polled
- [ ] Logs are visible and structured
- [ ] Environment variables properly set
- [ ] Security settings configured

## Next Steps

1. **Test the scraping API** with a real request
2. **Monitor the worker logs** during task execution
3. **Set up proper authentication** for production use
4. **Configure monitoring and alerting**
5. **Set up CI/CD** for automatic deployments

Your API should now be running on Railway with Celery background workers! 🚀
<｜tool▁calls▁begin｜><｜tool▁call▁begin｜>
grep
