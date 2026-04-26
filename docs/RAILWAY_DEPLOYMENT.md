# Railway Deployment Guide

## ⚠️ CRITICAL BEFORE DEPLOYING

### 1. **Rotate Gemini API Key** 🔑
Your API key was committed to git (visible in `.env`). 

**Action:**
1. Go to [Google AI Studio](https://aistudio.google.com/app/apikey)
3. Create a new API key
4. Add to Railway secrets (see below)

### 2. **Remove .env from Git History**
```bash
git rm --cached .env
git commit -m "Remove .env with exposed API key"
git push
```

## 📋 Railway Deployment Checklist

### Environment Variables
Set these in Railway Project Settings → Variables:

```
GEMINI_API_KEY=<your_new_key>
DASHBOARD_TOKEN=<long_random_token_required_for_public_deploys>
ENABLE_DANGEROUS_AUTOMATION=false
DEBUG=False
PORT=8000
```

### Database/Storage (Choose One)

**Option A: PostgreSQL** (Recommended for data persistence)
- Add Railway PostgreSQL plugin
- Create `schema.sql` to initialize tables
- Update `web_app.py` to use PostgreSQL instead of CSV files

**Option B: AWS S3** (For CSV/file storage)
- Add S3 bucket
- Set `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_S3_BUCKET`
- Update code to sync CSVs to S3

**Option C: Ephemeral** (No persistence)
- Data resets on each restart
- Only for testing/demo

### What's Fixed ✅
- ✅ `web_app.py` now uses `PORT` env var
- ✅ `debug=False` for production
- ✅ Gunicorn configured in `Procfile`
- ✅ `requirements.txt` updated with gunicorn
- ✅ `railway.json` corrected (removed hardcoded startCommand)

### Railway Deploy Steps

1. **Connect Git Repository**
   ```
   railway link
   ```

2. **Create Environment Variables**
   - DASHBOARD_TOKEN (required for any public deployment)
   - GEMINI_API_KEY (optional, only for AI cover letter generation)

3. **Deploy**
   - Push to master: `git push`
   - Railway auto-deploys from main branch

4. **Monitor**
   ```
   railway logs
   ```

## 🗄️ Data Persistence

**Current Issue:** CSVs are stored locally, will be lost on restart.

**Solutions:**

### For Local Testing:
```bash
export PYTHONUNBUFFERED=1  # Stream logs properly
python web_app.py
```

### For Production:
1. **Set up PostgreSQL** (Railway > Plugins > PostgreSQL)
2. **Update `web_app.py`** to use database instead of `.run_history.json`
3. **Use S3 or Railway Disk** for CSV uploads

## Port Configuration

Railway assigns a dynamic `PORT`. The app now reads from environment:
- Local: defaults to 5000
- Railway: uses `$PORT` variable automatically

## Monitoring & Logs

```bash
# View logs
railway logs -f

# Check environment variables
railway variables

# SSH into container
railway shell
```

## Rollback
```bash
railway rollback <deployment-id>
```

## Cost Estimate
- **Free tier**: 5GB RAM, enough for ~1000 companies
- **Beyond**: $5/month starter plan

## Next Steps
1. ✅ Create new Gemini API key
2. ✅ Set Railway environment variables
3. ✅ Choose data persistence method (PostgreSQL recommended)
4. ✅ Push to master branch
5. ✅ Monitor logs for errors
