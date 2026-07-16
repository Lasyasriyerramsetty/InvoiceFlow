# InvoiceFlow - Render Deployment Guide

## Overview
Deploy InvoiceFlow on Render with PostgreSQL, Redis, and background workers.

---

## Prerequisites
- GitHub repository connected to Render
- Render account (free tier available)
- Domain name (optional)

---

## Step 1: Deploy PostgreSQL Database

1. **Create Database**
   - Go to Render Dashboard → New → PostgreSQL
   - Name: `invoiceflow-db`
   - Database: `ap_invoice_db`
   - User: `ap_user`
   - Region: Choose closest to you
   - Plan: Free or Starter ($7/month)
   - Click **Create Database**

2. **Save Credentials**
   - Copy `Internal Database URL` (for backend)
   - Copy `External Database URL` (for local testing)

---

## Step 2: Deploy Redis

1. **Create Redis**
   - Go to Render Dashboard → New → Redis
   - Name: `invoiceflow-redis`
   - Plan: Free or Starter ($1/month)
   - Click **Create Redis**

2. **Save Connection URL**
   - Copy `Connection URL` (format: `redis://...`)

---

## Step 3: Deploy Backend (FastAPI)

1. **Create Web Service**
   - Go to Render Dashboard → New → Web Service
   - Connect your GitHub repository
   - Name: `invoiceflow-api`
   - Environment: `Python`
   - Build Command: 
     ```bash
     pip install -r backend/requirements.txt
     ```
   - Start Command:
     ```bash
     cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
     ```

2. **Set Environment Variables**
   ```env
   DATABASE_URL=<postgres-url-from-step-1>
   DATABASE_SYNC_URL=<same-but-with-psycopg2>
   REDIS_URL=<redis-url-from-step-2>
   CELERY_BROKER_URL=<redis-url-from-step-2>
   CELERY_RESULT_BACKEND=<redis-url-from-step-2>
   SECRET_KEY=<generate-random-32-char-string>
   JWT_SECRET_KEY=<generate-random-32-char-string>
   OPENAI_API_KEY=<your-openai-key>
   AZURE_DOCUMENT_INTELLIGENCE_ENDPOINT=<your-azure-endpoint>
   AZURE_DOCUMENT_INTELLIGENCE_KEY=<your-azure-key>
   ```
   Generate secret key:
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

3. **Configure Health Check**
   - Path: `/health`
   - Port: `8000`

4. **Create Celery Worker Service**
   - Repeat backend steps but with different commands:
   - Build Command: 
     ```bash
     pip install -r backend/requirements.txt
     ```
   - Start Command:
     ```bash
     cd backend && celery -A app.workers.celery_app worker --loglevel=info --concurrency=2
     ```
   - This runs background tasks

5. **Create Celery Beat Service (Optional)**
   - Start Command:
     ```bash
     cd backend && celery -A app.workers.celery_app beat --loglevel=info
     ```

---

## Step 4: Deploy Frontend (Next.js)

1. **Create Static Site / Web Service**
   - Go to Render Dashboard → New → Static Site
   - Connect your GitHub repository
   - Name: `invoiceflow-frontend`
   - Root Directory: `frontend`
   - Build Command:
     ```bash
     npm install && npm run build
     ```
   - Publish Directory: `frontend/.next/static`

2. **Set Environment Variables**
   ```env
   NEXT_PUBLIC_API_URL=https://invoiceflow-api.onrender.com
   NEXT_PUBLIC_APP_NAME=InvoiceFlow
   ```

3. **Add Next.js Config for Static Export**
   - Update `frontend/next.config.ts`:
     ```typescript
     const nextConfig = {
       output: 'export',
       images: { unoptimized: true },
       trailingSlash: true,
     };
     export default nextConfig;
     ```

4. **Deploy**
   - Click **Create Static Site**
   - Render will build and deploy

---

## Step 5: Run Database Migrations

1. **Create One-Time Job**
   - Dashboard → New → Background Job
   - Name: `invoiceflow-migrations`
   - Command:
     ```bash
     cd backend && alembic upgrade head
     ```
   - Environment variables: Same as backend

2. **Run Job**
   - Click **Run Job**
   - Wait for completion

---

## Step 6: Seed Initial Data (Optional)

1. **Create Seed Job**
   - Dashboard → New → Background Job
   - Name: `invoiceflow-seed`
   - Command:
     ```bash
     cd backend && python -m app.infrastructure.database.seed
     ```
   - Environment variables: Same as backend

2. **Run Job**
   - Click **Run Job**

---

## Step 7: Domain & SSL

### Custom Domain (Optional)
1. **Frontend:** Settings → Custom Domains → Add Domain
   - Add: `app.yourdomain.com`
   - Render provides SSL automatically

2. **Backend:** Same process for API subdomain
   - Add: `api.yourdomain.com`

### Update CORS
- Update `backend/app/core/config.py`:
  ```python
  cors_origins: list[str] = [
      "https://invoiceflow-frontend.onrender.com",
      "https://app.yourdomain.com"
  ]
  ```

---

## Step 8: Verify Deployment

1. **Check Backend Health**
   ```bash
   curl https://invoiceflow-api.onrender.com/health
   ```
   Expected: `{"status":"healthy",...}`

2. **Check Frontend**
   - Visit: `https://invoiceflow-frontend.onrender.com`
   - Should load InvoiceFlow dashboard

3. **Test Upload**
   - Go to Upload Center
   - Upload a test invoice
   - Verify processing completes

---

## Step 9: Configure File Storage

### Option A: Local Storage (Simple)
- Files stored in Render's filesystem
- **Warning:** Files lost on redeploy
- Good for testing only

### Option B: Cloudflare R2 (Recommended)
1. Create R2 bucket
2. Update `MINIO_ENDPOINT` to R2 endpoint
3. Update `MINIO_ACCESS_KEY` and `MINIO_SECRET_KEY`
4. Files persist across deploys

### Option C: AWS S3
1. Create S3 bucket
2. Update MinIO settings to S3
3. Update credentials in Render environment

---

## Step 10: Monitoring & Logs

### Enable Logs
- Each service has **Logs** tab in Render
- Monitor for errors

### Metrics
- Render provides basic metrics
- Enable **Advanced Metrics** for detailed monitoring

### Alerts (Optional)
- Set up email alerts for downtime
- Configure in Render settings

---

## Cost Estimate

### Free Tier (Development)
- Frontend: Free
- Backend: Free (sleeps after 15 min)
- PostgreSQL: Free (90 days)
- Redis: Free
- **Total: $0**

### Starter Tier (Production)
- Frontend: $0 (static)
- Backend: $7/month
- Worker: $7/month
- PostgreSQL: $7/month
- Redis: $1/month
- **Total: ~$22/month**

### Pro Tier (Scale)
- Backend: $25/month (more RAM/CPU)
- Worker: $25/month
- PostgreSQL: $50/month
- Redis: $5/month
- **Total: ~$105/month**

---

## Troubleshooting

### Issue: Backend Won't Start
**Check:**
- Logs in Render dashboard
- Database URL format
- Environment variables set correctly

### Issue: Frontend Can't Connect to Backend
**Check:**
- `NEXT_PUBLIC_API_URL` is set correctly
- CORS includes frontend domain
- Backend is running

### Issue: Uploads Fail
**Check:**
- File size limits
- Storage configuration
- Backend logs for errors

### Issue: Celery Tasks Not Running
**Check:**
- Redis connection
- Celery worker logs
- Broker URL format

---

## Quick Reference

| Service | Type | Plan | Monthly Cost |
|---------|------|------|--------------|
| Frontend | Static Site | Free | $0 |
| Backend | Web Service | Starter | $7 |
| Worker | Background Worker | Starter | $7 |
| PostgreSQL | Database | Starter | $7 |
| Redis | Cache | Free | $0 |
| **Total (Starter)** | | | **$21/month** |

---

## Alternative: Single Service Deployment

If you want cheaper/simpler deployment:

1. **Use Railway instead** - better for full-stack
2. **Use Docket Compose on VPS** - $5 VPS runs everything
3. **Use AWS App Runner** - pay per use

---

## Support

- Render Docs: https://render.com/docs
- FastAPI Deployment: https://fastapi.tiangolo.com/deployment/
- Next.js Deployment: https://nextjs.org/docs/pages/guides/deployment

**Need Help?** Check Render logs first, they show detailed errors.