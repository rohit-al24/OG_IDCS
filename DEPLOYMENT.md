# Deployment Guide for IDCS Application

## Prerequisites
- Python 3.11+
- PostgreSQL (for production)
- Git
- Server with Ubuntu/Debian (recommended)

## Pre-Deployment Checklist

### 1. Environment Setup
Create a `.env` file in the root directory:
```bash
cp .env.example .env
```

Edit `.env` with your production values:
```env
SECRET_KEY=your-unique-secret-key-here-generate-with-django
DEBUG=False
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,your-server-ip

# Database
DB_ENGINE=django.db.backends.postgresql
DB_NAME=idcs_db
DB_USER=idcs_user
DB_PASSWORD=secure-password-here
DB_HOST=localhost
DB_PORT=5432

# Email
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
```

### 2. Generate a Secure SECRET_KEY
```bash
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

---

## Deployment Options

### Option 1: Traditional VPS Deployment (Ubuntu/Debian)

#### Step 1: Update System
```bash
sudo apt update && sudo apt upgrade -y
```

#### Step 2: Install Dependencies
```bash
sudo apt install -y python3.11 python3.11-venv python3-pip postgresql postgresql-contrib nginx
```

#### Step 3: Setup PostgreSQL
```bash
sudo -u postgres psql
```

In PostgreSQL shell:
```sql
CREATE DATABASE idcs_db;
CREATE USER idcs_user WITH PASSWORD 'your-secure-password';
ALTER ROLE idcs_user SET client_encoding TO 'utf8';
ALTER ROLE idcs_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE idcs_user SET timezone TO 'Asia/Kolkata';
GRANT ALL PRIVILEGES ON DATABASE idcs_db TO idcs_user;
\q
```

#### Step 4: Clone and Setup Application
```bash
cd /var/www/
sudo git clone <your-repo-url> idcs
cd idcs
sudo chown -R $USER:$USER /var/www/idcs
```

#### Step 5: Create Virtual Environment
```bash
python3.11 -m venv venv
source venv/bin/activate
```

#### Step 6: Install Python Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

#### Step 7: Configure Environment
```bash
# Create and edit .env file with production settings
nano .env
```

#### Step 8: Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

#### Step 9: Create Superuser
```bash
python manage.py createsuperuser
```

#### Step 10: Collect Static Files
```bash
python manage.py collectstatic --noinput
```

#### Step 11: Configure Gunicorn Service
Create `/etc/systemd/system/idcs.service`:
```ini
[Unit]
Description=IDCS Gunicorn daemon
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/idcs
EnvironmentFile=/var/www/idcs/.env
ExecStart=/var/www/idcs/venv/bin/gunicorn \
    --workers 3 \
    --bind unix:/var/www/idcs/gunicorn.sock \
    backend.wsgi:application

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable idcs
sudo systemctl start idcs
sudo systemctl status idcs
```

#### Step 12: Configure Nginx
Create `/etc/nginx/sites-available/idcs`:
```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    client_max_body_size 100M;

    location = /favicon.ico { access_log off; log_not_found off; }
    
    location /static/ {
        alias /var/www/idcs/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /var/www/idcs/media/;
        expires 30d;
        add_header Cache-Control "public";
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:/var/www/idcs/gunicorn.sock;
    }
}
```

Enable site:
```bash
sudo ln -s /etc/nginx/sites-available/idcs /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### Step 13: Setup SSL with Let's Encrypt (Optional but Recommended)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

---

### Option 2: Docker Deployment

#### Step 1: Install Docker and Docker Compose
```bash
sudo apt update
sudo apt install docker.io docker-compose -y
sudo systemctl enable docker
sudo systemctl start docker
```

#### Step 2: Configure Environment
```bash
cp .env.example .env
# Edit .env with production values
nano .env
```

#### Step 3: Build and Run
```bash
docker-compose up -d --build
```

#### Step 4: Run Migrations
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
docker-compose exec web python manage.py collectstatic --noinput
```

#### Step 5: View Logs
```bash
docker-compose logs -f
```

---

### Option 3: Heroku Deployment

#### Step 1: Install Heroku CLI
```bash
curl https://cli-assets.heroku.com/install.sh | sh
```

#### Step 2: Login and Create App
```bash
heroku login
heroku create your-app-name
```

#### Step 3: Add PostgreSQL
```bash
heroku addons:create heroku-postgresql:mini
```

#### Step 4: Set Environment Variables
```bash
heroku config:set SECRET_KEY='your-secret-key'
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS=your-app-name.herokuapp.com
```

#### Step 5: Deploy
```bash
git push heroku master
```

#### Step 6: Run Migrations
```bash
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

---

### Option 4: AWS/DigitalOcean/Linode
Follow Option 1 (Traditional VPS) instructions on your cloud VM.

---

## Post-Deployment Tasks

### 1. Test Application
- Visit your domain
- Test login/logout
- Test file uploads
- Test email functionality
- Check all pages load correctly

### 2. Setup Monitoring
- Configure logging
- Setup error tracking (e.g., Sentry)
- Monitor server resources

### 3. Setup Backups
```bash
# Database backup script
#!/bin/bash
pg_dump -U idcs_user idcs_db > backup_$(date +%Y%m%d_%H%M%S).sql
```

### 4. Regular Maintenance
```bash
# Update application
cd /var/www/idcs
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart idcs
```

---

## Troubleshooting

### Check Logs
```bash
# Application logs
sudo journalctl -u idcs -f

# Nginx logs
sudo tail -f /var/log/nginx/error.log

# Docker logs
docker-compose logs -f web
```

### Common Issues

1. **Static files not loading**
   - Run `python manage.py collectstatic --noinput`
   - Check nginx configuration
   - Verify file permissions

2. **Database connection errors**
   - Verify PostgreSQL is running
   - Check `.env` database credentials
   - Ensure database exists

3. **502 Bad Gateway**
   - Check gunicorn is running: `sudo systemctl status idcs`
   - Verify socket file exists
   - Check nginx error logs

---

## Security Recommendations

1. ✅ Keep `DEBUG=False` in production
2. ✅ Use strong `SECRET_KEY`
3. ✅ Use HTTPS (SSL certificate)
4. ✅ Regularly update dependencies
5. ✅ Use PostgreSQL instead of SQLite
6. ✅ Set proper `ALLOWED_HOSTS`
7. ✅ Use environment variables for secrets
8. ✅ Regular backups
9. ✅ Monitor logs and errors
10. ✅ Keep system updated

---

## Support
For issues, check logs and documentation. Update `.env` settings as needed.
