# ClinIQ Deployment Guide

## Quick Deployment Overview

### Backend Options
- **Railway** (Recommended) - Auto-deploy from Git
- **Render** - Free tier available
- **AWS Lambda** - Serverless option

### Frontend Options
- **Vercel** (Recommended) - Zero-config deployment
- **Netlify** - Continuous deployment
- **Cloudflare Pages** - Fast global CDN

---

## Backend Deployment - Railway

### 1. Prepare Backend

Create `backend/Procfile`:
```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Create `backend/runtime.txt`:
```
python-3.11
```

### 2. Deploy to Railway

1. Push code to GitHub
2. Go to [railway.app](https://railway.app)
3. Click **"New Project"** → **"Deploy from GitHub repo"**
4. Select your repository
5. Set **Root Directory:** `backend`
6. Add environment variables:
   ```
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_anon_key
   SUPABASE_SERVICE_KEY=your_service_key
   JWT_SECRET_KEY=your_secret_key
   JWT_ALGORITHM=HS256
   JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
   ENVIRONMENT=production
   CORS_ORIGINS=["https://your-frontend.vercel.app"]
   ```
7. Click **"Deploy"**

Note your deployment URL: `https://your-app.railway.app`

---

## Frontend Deployment - Vercel

### 1. Prepare Frontend

Create `frontend/vercel.json`:
```json
{
  "buildCommand": "pnpm build",
  "outputDirectory": "dist",
  "framework": "vite"
}
```

### 2. Deploy to Vercel

1. Push code to GitHub
2. Go to [vercel.com](https://vercel.com)
3. Click **"New Project"**
4. Import your GitHub repository
5. Set **Root Directory:** `frontend`
6. Add environment variable:
   ```
   VITE_API_BASE_URL=https://your-app.railway.app
   ```
7. Click **"Deploy"**

Your app will be live at: `https://your-app.vercel.app`

---

## Alternative: Backend on Render

1. Go to [render.com](https://render.com)
2. Click **"New"** → **"Web Service"**
3. Connect GitHub repo
4. Settings:
   - **Name:** `cliniq-api`
   - **Root Directory:** `backend`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Add same environment variables as Railway
6. Click **"Create Web Service"**

---

## Post-Deployment Checklist

### Backend
- [ ] All environment variables set correctly
- [ ] Supabase connection working
- [ ] CORS configured for frontend domain
- [ ] API docs accessible at `/docs`
- [ ] Health check passing at `/health`

### Frontend
- [ ] API base URL points to production backend
- [ ] Login working
- [ ] Can fetch and display patients
- [ ] File uploads working
- [ ] All routes accessible

### Security
- [ ] JWT secret is secure random string
- [ ] Service role key never exposed to frontend
- [ ] HTTPS enabled on both frontend and backend
- [ ] CORS restricted to your domains only

---

## Environment Variables Summary

### Backend Production
```env
SUPABASE_URL=https://xxx.supabase.co
SUPABASE_KEY=eyJ... (anon key - safe for frontend)
SUPABASE_SERVICE_KEY=eyJ... (KEEP SECRET!)
JWT_SECRET_KEY=<64-char-random-string>
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=1440
ENVIRONMENT=production
CORS_ORIGINS=["https://your-frontend.vercel.app","https://your-frontend.netlify.app"]
```

### Frontend Production
```env
VITE_API_BASE_URL=https://your-backend.railway.app
```

---

## Monitoring & Maintenance

### Check Backend Health
```bash
curl https://your-backend.railway.app/health
```

### Check API Documentation
Visit: `https://your-backend.railway.app/docs`

### View Logs
- **Railway:** Dashboard → Logs tab
- **Render:** Dashboard → Logs
- **Vercel:** Dashboard → Deployments → Function Logs

### Database Monitoring
Check Supabase Dashboard:
- Database health
- Query performance
- Storage usage
- API usage limits

---

## Troubleshooting

### Backend 502/503 Errors
- Check environment variables are set
- Verify Supabase connection
- Check service logs for Python errors
- Ensure all dependencies in requirements.txt

### Frontend Build Failures
- Check Node version matches .mise.toml
- Verify all dependencies installed
- Check for TypeScript errors
- Ensure API URL is set correctly

### CORS Errors
- Add frontend URL to CORS_ORIGINS in backend
- Format: `["https://app.vercel.app"]` (valid JSON array)
- Redeploy backend after changing

### Authentication Issues
- Verify JWT_SECRET_KEY matches between deployments
- Check token expiration settings
- Ensure Supabase keys are correct
- Test login endpoint directly: `/auth/login`

---

## Scaling Considerations

### Database (Supabase)
- Free tier: 500MB database, 1GB file storage
- Upgrade for more connections and storage
- Set up database indexes for performance
- Enable read replicas for high traffic

### Backend
- Railway scales automatically
- Add horizontal scaling for high load
- Consider caching layer (Redis)
- Monitor response times

### Frontend
- Vercel/Netlify have global CDN
- Optimize images and assets
- Enable compression
- Use code splitting

---

## Cost Estimates

### Free Tier
- **Supabase:** Free up to 500MB DB
- **Railway:** $5 credit/month
- **Vercel:** 100GB bandwidth/month free
- **Total:** ~$5-10/month

### Production (Small Clinic)
- **Supabase Pro:** $25/month
- **Railway:** ~$15/month
- **Vercel Pro:** $20/month  
- **Total:** ~$60/month

---

## Backup Strategy

### Database Backups
1. Supabase automatic daily backups (Pro plan)
2. Manual export: Supabase Dashboard → Database → Backups
3. Schedule weekly exports to external storage

### File Storage Backups
1. Download Supabase storage bucket contents
2. Use Supabase CLI for automated backups
3. Store in S3 or Google Cloud Storage

---

**Need help?** Check deployment platform documentation or Supabase support.
