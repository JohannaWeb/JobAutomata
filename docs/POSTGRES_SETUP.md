# PostgreSQL Setup for Railway

## Local Development

### 1. Install PostgreSQL
```bash
# macOS
brew install postgresql

# Linux
sudo apt-get install postgresql postgresql-contrib

# Windows
# Download from https://www.postgresql.org/download/windows/
```

### 2. Create Local Database
```bash
# Start PostgreSQL
pg_ctl -D /usr/local/var/postgres start

# Create database
createdb jobautomata

# Set environment variable
export DATABASE_URL="postgresql://localhost/jobautomata"
```

### 3. Initialize Schema
```bash
python db_init.py
```

### 4. Run App
```bash
python web_app.py
```

---

## Railway Deployment

### 1. Add PostgreSQL to Railway

1. Go to your Railway project
2. Click "Add" → "Add Service"
3. Select "PostgreSQL"
4. Railway will auto-create and inject `DATABASE_URL`

### 2. Get Connection String

Once PostgreSQL is added to Railway, it automatically provides `DATABASE_URL` in your project environment.

### 3. Run Database Migrations

Before deploying the app, run the initialization:

**Option A: Via Railway Shell**
```bash
railway shell
python db_init.py
exit
```

**Option B: Via Railway CLI**
```bash
# Build and run init script
railway up
# After deployment succeeds, run:
railway run python db_init.py
```

### 4. Deploy App

```bash
git add -A
git commit -m "Add PostgreSQL support"
git push
```

Railway will automatically:
- Read `DATABASE_URL` from PostgreSQL plugin
- Install dependencies from `requirements.txt`
- Run `gunicorn` via `Procfile`

### 5. Verify

```bash
railway logs -f

# Look for:
# "Starting Job Automata Web Dashboard"
# No database errors
```

---

## Data Flow

**Before** (File-based):
```
CSV Files → Parse → Memory → Return
   ↓
Ephemeral (lost on restart)
```

**After** (PostgreSQL):
```
CSV Files → Migration → PostgreSQL ← App Queries
   ↓
Persistent (survives restarts)
```

---

## Troubleshooting

### "database connection refused"
- Check Railway PostgreSQL service is running
- Verify `DATABASE_URL` is set in Railway variables
- Check logs: `railway logs -f`

### "relation does not exist"
- Schema wasn't initialized
- Run: `railway run python db_init.py`

### Want to Reset Database?
```bash
# Via Railway shell
railway shell
psql $DATABASE_URL
DROP TABLE companies, applications, run_history, cvs, config;
python db_init.py
```

---

## Backup & Restore

### Export Data
```bash
railway run pg_dump $DATABASE_URL > backup.sql
```

### Restore Data
```bash
railway run psql $DATABASE_URL < backup.sql
```

---

## Monitoring

### View Database Size
```bash
railway shell
psql $DATABASE_URL -c "SELECT pg_size_pretty(pg_database_size(current_database()));"
```

### Check Record Counts
```bash
railway shell
psql $DATABASE_URL -c "SELECT 
  (SELECT COUNT(*) FROM companies) as companies,
  (SELECT COUNT(*) FROM applications) as applications,
  (SELECT COUNT(*) FROM run_history) as runs;"
```

---

## Performance Tips

1. **Indexes** are already created in `schema.sql`
2. **Connection pooling** will be added automatically by Railway
3. **Backups** are handled by Railway (automatic daily)

---

Done! Your app now has persistent data. 🚀
