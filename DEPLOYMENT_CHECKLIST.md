# 🚀 Quick Deployment Checklist

## ✅ Pre-Deployment Changes (COMPLETED)

- [x] Added environment variable support with `python-decouple`
- [x] Moved sensitive data to `.env` file
- [x] Updated `DEBUG` to use environment variable
- [x] Updated `SECRET_KEY` to use environment variable
- [x] Updated `ALLOWED_HOSTS` to use environment variable
- [x] Updated database configuration for PostgreSQL support
- [x] Updated email credentials to use environment variables
- [x] Added `whitenoise` for static file serving
- [x] Added `gunicorn` as WSGI server
- [x] Added security headers for production
- [x] Created `.env.example` template
- [x] Created `Procfile` for Heroku
- [x] Created `Dockerfile` and `docker-compose.yml`
- [x] Created `nginx.conf` for reverse proxy
- [x] Updated `.gitignore` for security
- [x] Created comprehensive `DEPLOYMENT.md` guide

## 📋 Before You Deploy - MUST DO

### 1. Create `.env` file
```bash
cp .env.example .env
```

### 2. Generate SECRET_KEY
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```
Copy the output to your `.env` file's `SECRET_KEY`

### 3. Update `.env` with your values
- Set `DEBUG=False` for production
- Set `ALLOWED_HOSTS` to your domain(s)
- Configure database credentials (PostgreSQL recommended)
- Update email credentials with your own

### 4. Install new dependencies
```bash
pip install -r requirements.txt
```

### 5. Test locally with production settings
```bash
# Set DEBUG=False in .env
python manage.py collectstatic --noinput
gunicorn backend.wsgi:application
```

### 6. Setup PostgreSQL database
For production, replace SQLite with PostgreSQL:
- Install PostgreSQL
- Create database and user
- Update `.env` with database credentials

### 7. Run migrations on production server
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

## ⚠️ IMPORTANT SECURITY NOTES

1. **NEVER commit `.env` file** - It's in `.gitignore`
2. **Change SECRET_KEY** - Generate a new one
3. **Update EMAIL credentials** - Currently has hardcoded values as fallback
4. **Use PostgreSQL** - SQLite is not recommended for production
5. **Set DEBUG=False** - Critical for security
6. **Configure ALLOWED_HOSTS** - Only allow your domain(s)

## 🎯 Quick Deploy Commands

### Local Testing
```bash
python manage.py runserver
```

### Production with Gunicorn
```bash
gunicorn backend.wsgi:application --bind 0.0.0.0:8000
```

### Docker
```bash
docker-compose up -d --build
```

### Heroku
```bash
git push heroku master
```

## 📚 Next Steps

1. Read `DEPLOYMENT.md` for detailed deployment instructions
2. Choose your deployment platform (VPS, Docker, Heroku, etc.)
3. Follow the specific platform's section in `DEPLOYMENT.md`
4. Test thoroughly after deployment
5. Setup monitoring and backups

## 🔧 Files Modified/Created

### Modified:
- `backend/settings.py` - Environment variables, security, static files
- `requirements.txt` - Added whitenoise, gunicorn, python-dotenv
- `.gitignore` - Enhanced security exclusions

### Created:
- `.env.example` - Environment variables template
- `Procfile` - For Heroku deployment
- `runtime.txt` - Python version for Heroku
- `Dockerfile` - For Docker deployment
- `docker-compose.yml` - Multi-container setup
- `nginx.conf` - Reverse proxy configuration
- `.dockerignore` - Docker build exclusions
- `DEPLOYMENT.md` - Comprehensive deployment guide
- `DEPLOYMENT_CHECKLIST.md` - This file

## 🆘 Need Help?

Check `DEPLOYMENT.md` for:
- Detailed deployment steps for various platforms
- Troubleshooting common issues
- Security best practices
- Monitoring and maintenance tips

## 🔁 Render (render.com) — recommended quick checklist

If you're deploying to Render, follow these steps to ensure migrations run and the service uses a persistent Postgres database.

1. Provision a Postgres database on Render (or use Supabase) and copy the DATABASE_URL connection string.

2. In your Render Web Service settings, add the following environment variables:
	- DATABASE_URL=<your_postgres_database_url>
	- SECRET_KEY=<a-strong-secret-generated-by-django>
	- DEBUG=False
	- ALLOWED_HOSTS=<your-domain.com> (or set in settings via env)

3. Set the Start Command for the Render Web Service to run migrations, collect static files, and start Gunicorn. Use this exact Start Command:

```bash
bash -lc "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT"
```

This makes sure database tables (including `core_notice`) are created before the app serves traffic.

4. (Optional) Run a one-off shell on Render and verify migrations manually:

```bash
python manage.py migrate
python manage.py showmigrations
```

5. Redeploy the service. If you used `DEBUG=False` and a valid `SECRET_KEY`, Django's production security settings will be active.

Notes:
- Do not use SQLite on Render for production — use Postgres.
- Keep your `SECRET_KEY` and DB credentials secret. Use Render's Secrets/Environment variables UI.
- After a successful deploy, remove the temporary guard in `core/views.py` that catches missing tables (we added it to prevent a 500 during initial migration).

Optional: AUTO_MIGRATE environment variable

If you don't want to modify the Start Command, you can enable automatic migrations at WSGI startup by setting the environment variable `AUTO_MIGRATE=true`. The application will attempt to run `manage.py migrate` during WSGI initialisation. This is convenient but you should still prefer running migrations explicitly during deploy.

## ⚠️ Deploying with SQLite on Render (NOT recommended) — if you must

If you intend to deploy using the bundled `db.sqlite3`, you can make it work, but be aware of the limitations:

- Render's filesystem is ephemeral. Any writes to `db.sqlite3` will be lost on deploy or instance restart. Backups are your responsibility.
- SQLite does not support concurrent writes from multiple processes/instances. Use a single-instance service and avoid scaling horizontally.
- Using SQLite in production can lead to corruption under load. Prefer Postgres for anything beyond testing or very low-traffic sites.

Steps to deploy with SQLite on Render (quick):

1. Do NOT set `DATABASE_URL` in Render environment variables (leave it unset so the app falls back to SQLite as configured in `backend/settings.py`).

2. Add the required environment variables in Render:
	- SECRET_KEY=<generate-and-paste-secret>
	- DEBUG=False (or leave True for testing, but False for production)
	- ALLOWED_HOSTS=<your-domain.com>

3. Use this Start Command for the Web Service (this runs migrations against the local sqlite file, collects static, then starts Gunicorn):

```bash
bash -lc "python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn backend.wsgi:application --bind 0.0.0.0:$PORT"
```

4. (Optional) If you prefer to initialize the DB manually once, open a Render Shell/one-off command and run:

```bash
python manage.py migrate
python manage.py createsuperuser
```

5. After deployment, monitor the instance and create backups of `db.sqlite3` regularly if you care about persistence. You can download the file via the Render shell and store it in external storage.

Reminder: This SQLite route is useful for quick demos or staging, but for a resilient production site you should migrate to Postgres and follow the main Render checklist above.
