# OJS Security Scanner - Automated Scanning & Email Reports Setup Guide

Panduan lengkap untuk mengatur automated scanning setiap 6 jam dengan laporan HTML yang dikirim via email.

## Fitur Baru (New Features)

✅ **Automated Scanning** - Scan otomatis setiap 6 jam (dapat dikonfigurasi)
✅ **HTML Reports** - Laporan HTML yang cantik dan interaktif
✅ **Email Notifications** - Kirim laporan langsung ke email Anda
✅ **Background Scheduler** - Berjalan otomatis di background tanpa perlu trigger manual
✅ **Report Management** - Akses semua laporan melalui dashboard

---

## Prerequisites (Persyaratan)

- Python 3.12+
- FastAPI
- APScheduler (untuk scheduling)
- SMTP Server access (untuk mengirim email)

---

## 1. Konfigurasi Email (Email Configuration)

### 1.1 Menggunakan Gmail

**Step 1: Aktifkan 2-Factor Authentication (2FA) di Gmail**
1. Buka https://myaccount.google.com/security
2. Aktifkan "2-Step Verification"

**Step 2: Generate App Password**
1. Kembali ke Security settings (https://myaccount.google.com/security)
2. Cari "App passwords" (muncul setelah 2FA aktif)
3. Pilih "Mail" dan "Windows Computer"
4. Copy password yang dibuat

**Step 3: Konfigurasi `.env`**
```env
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=xxxx xxxx xxxx xxxx  # Paste app password here (without spaces)
```

### 1.2 Menggunakan Email Provider Lain

Contoh untuk Outlook/Microsoft:
```env
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SENDER_EMAIL=your-email@outlook.com
SENDER_PASSWORD=your-password
```

Contoh untuk Yahoo:
```env
SMTP_SERVER=smtp.mail.yahoo.com
SMTP_PORT=587
SENDER_EMAIL=your-email@yahoo.com
SENDER_PASSWORD=your-app-password
```

---

## 2. Konfigurasi Automated Scanning

Edit file `.env` Anda:

```env
# Enable scheduler (true/false)
ENABLE_SCHEDULER=true

# Interval scan dalam jam (default: 6)
SCAN_INTERVAL_HOURS=6

# Path OJS source
OJS_SOURCE_PATH=ojs/ojs-main
```

### Interval Presets

| Interval | Konfigurasi | Use Case |
|----------|-----------|----------|
| Setiap jam | `SCAN_INTERVAL_HOURS=1` | Development/Testing |
| Setiap 2 jam | `SCAN_INTERVAL_HOURS=2` | High security environments |
| Setiap 6 jam | `SCAN_INTERVAL_HOURS=6` | Default (recommended) |
| Setiap 12 jam | `SCAN_INTERVAL_HOURS=12` | Normal production |
| Setiap hari | `SCAN_INTERVAL_HOURS=24` | Low-frequency checks |

---

## 3. Setup User Email Preferences

Pengguna harus mengkonfigurasi email mereka untuk menerima laporan.

### 3.1 Register & Login
```bash
# Register user baru
curl -X POST "http://localhost:8000/auth/register?username=admin&password=admin123"
# Response: {"status": "success", "token": "xxx"}

# Login
curl -X POST "http://localhost:8000/auth/login?username=admin&password=admin123"
# Response: {"status": "success", "token": "xxx"}
```

### 3.2 Konfigurasi Email di User
```bash
curl -X POST "http://localhost:8000/auth/email-settings?token=YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@gmail.com",
    "receive_reports": true
  }'
```

### 3.3 Cek Email Settings
```bash
curl "http://localhost:8000/auth/email-settings?token=YOUR_TOKEN"
```

---

## 4. Akses Laporan HTML

### 4.1 Melihat Daftar Laporan
```bash
curl "http://localhost:8000/reports/list"
```

Response:
```json
{
  "status": "success",
  "total": 5,
  "reports": [
    {
      "id": 5,
      "target": "ojs/ojs-main",
      "timestamp": "2024-01-15 10:30:00",
      "source": "PKP OJS SAST Agent (Scheduled)",
      "is_scheduled": true,
      "html_report_available": true,
      "html_report_path": "/reports/scan_report_5_20240115_103000.html"
    }
  ]
}
```

### 4.2 Membuka Laporan HTML di Browser
Akses langsung: `http://localhost:8000/reports/{scan_id}/html`

Contoh: `http://localhost:8000/reports/5/html`

### 4.3 Download Laporan
```bash
curl -O "http://localhost:8000/reports/5/download"
```

### 4.4 Info Laporan
```bash
curl "http://localhost:8000/reports/5/info"
```

---

## 5. API Endpoints

### Scheduler
```
GET /scheduler/status
```
Get current scheduler status dan next run time.

### Reports
```
GET /reports/list                 # List all reports
GET /reports/{scan_id}/html       # View HTML report
GET /reports/{scan_id}/info       # Get report info
GET /reports/{scan_id}/download   # Download HTML report
```

### Auth
```
POST /auth/register               # Register user
POST /auth/login                  # Login user
POST /auth/email-settings         # Update email settings
GET /auth/email-settings          # Get email settings
```

### Scan
```
POST /scan/                       # Manual scan
GET /scan/history                 # Get scan history
GET /scan/report/{scan_id}        # Download PDF report
```

---

## 6. Docker Setup

### 6.1 Build & Run dengan Docker Compose

Update `docker-compose.yml`:

```yaml
scanner-api:
  build:
    context: .
    dockerfile: Dockerfile.api
  container_name: ojs-scanner-api
  ports:
    - "8000:8000"
  volumes:
    - ./ojs/ojs-main:/ojs:ro
    - ./ojs_scanner.db:/app/ojs_scanner.db
    - ./reports:/app/reports  # Persist reports
  environment:
    OJS_SOURCE_PATH: /ojs
    ENABLE_SCHEDULER: "true"
    SCAN_INTERVAL_HOURS: 6
    SMTP_SERVER: smtp.gmail.com
    SMTP_PORT: 587
    SENDER_EMAIL: ${SENDER_EMAIL}
    SENDER_PASSWORD: ${SENDER_PASSWORD}
    SEMGREP_ENABLED: "true"
    SEMGREP_TIMEOUT_SECONDS: 90
  depends_on:
    - ojs
```

### 6.2 Run dengan Docker
```bash
docker-compose up -d
```

### 6.3 Check Logs
```bash
docker-compose logs -f scanner-api
```

---

## 7. Monitoring & Troubleshooting

### 7.1 Check Scheduler Status
```bash
curl http://localhost:8000/scheduler/status
```

Expected output:
```json
{
  "running": true,
  "jobs": [
    {
      "id": "scheduled_scan",
      "name": "Scheduled OJS Security Scan",
      "trigger": "interval[6:00:00]",
      "next_run_time": "2024-01-15 16:30:00+00:00"
    }
  ]
}
```

### 7.2 Logs
Check application logs untuk debug:
```bash
# Docker
docker-compose logs -f scanner-api

# Local
python -m uvicorn backend.main:app --reload
```

### 7.3 Troubleshooting Email

**Email tidak terkirim?**

1. Pastikan `.env` sudah dikonfigurasi dengan benar:
   ```bash
   cat .env | grep SMTP
   cat .env | grep SENDER
   ```

2. Test koneksi SMTP:
   ```python
   import smtplib
   try:
       server = smtplib.SMTP("smtp.gmail.com", 587)
       server.starttls()
       server.login("your-email@gmail.com", "your-app-password")
       print("SMTP connection successful!")
   except Exception as e:
       print(f"Error: {e}")
   ```

3. Pastikan user sudah set email dan `receive_reports=true`:
   ```bash
   curl http://localhost:8000/auth/email-settings?token=YOUR_TOKEN
   ```

4. Check database untuk scan record:
   ```bash
   sqlite3 ojs_scanner.db "SELECT * FROM scans ORDER BY timestamp DESC LIMIT 5;"
   ```

### 7.4 Troubleshooting Scheduler

**Scheduler tidak berjalan?**

1. Check apakah scheduler enabled:
   ```bash
   echo $ENABLE_SCHEDULER  # Should be 'true'
   ```

2. Check scheduler logs:
   ```bash
   docker-compose logs scanner-api | grep -i scheduler
   ```

3. Verify interval config:
   ```bash
   curl http://localhost:8000/scheduler/status
   ```

---

## 8. Database Schema Updates

Setelah update, jalankan migration:

```bash
# The app akan otomatis create tables saat startup
python -c "from backend.database import engine, Base; Base.metadata.create_all(bind=engine)"
```

**New columns di `users` table:**
- `email` (VARCHAR 255, nullable)
- `receive_reports` (BOOLEAN, default=false)

**New columns di `scans` table:**
- `is_scheduled` (BOOLEAN, default=false)
- `html_report_path` (VARCHAR 255, nullable)

---

## 9. Contoh Workflow Lengkap

### Setup Initial

```bash
# 1. Copy .env.example ke .env
cp .env.example .env

# 2. Edit .env dengan email Anda
# (Configure SMTP_SERVER, SMTP_PORT, SENDER_EMAIL, SENDER_PASSWORD)

# 3. Install dependencies
pip install -r requirements.txt

# 4. Start application
python -m uvicorn backend.main:app --reload
```

### Register & Configure User

```bash
# 1. Register
TOKEN=$(curl -s -X POST "http://localhost:8000/auth/register?username=admin&password=admin123" | jq -r '.token')

# 2. Set email settings
curl -X POST "http://localhost:8000/auth/email-settings?token=$TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@gmail.com",
    "receive_reports": true
  }'

# 3. Verify
curl "http://localhost:8000/auth/email-settings?token=$TOKEN"
```

### Monitor Scans

```bash
# 1. Check scheduler status
curl http://localhost:8000/scheduler/status

# 2. View reports
curl http://localhost:8000/reports/list

# 3. Open report in browser
# http://localhost:8000/reports/1/html
```

---

## 10. File Structure

```
backend/
├── models/
│   ├── scan.py          # Updated: add is_scheduled, html_report_path
│   ├── user.py          # Updated: add email, receive_reports
│   └── vulnerability.py
├── routers/
│   ├── auth.py          # Updated: add email settings endpoints
│   ├── scan.py          # Updated: generate HTML reports
│   └── reports.py       # NEW: report access endpoints
├── services/
│   ├── html_report_service.py      # NEW: HTML report generation
│   ├── email_service.py            # NEW: Email sending
│   ├── scheduler_service.py        # NEW: Automated scheduling
│   └── ...
└── main.py              # Updated: init scheduler on startup
```

---

## 11. Features Summary

| Fitur | Status | Deskripsi |
|-------|--------|-----------|
| Automated Scanning | ✅ | Scan otomatis setiap N jam |
| HTML Reports | ✅ | Laporan HTML yang beautiful |
| Email Notification | ✅ | Kirim laporan via email |
| Report Management | ✅ | View/download laporan |
| Background Scheduler | ✅ | Berjalan di background |
| User Email Settings | ✅ | Customize per user |
| Scheduler Status API | ✅ | Monitor scheduler |
| Report History | ✅ | Simpan semua laporan |

---

## Support & Issues

Jika ada masalah:

1. Check logs: `docker-compose logs scanner-api`
2. Verify `.env` configuration
3. Test email settings manually
4. Check database integrity

---

**Last Updated:** 2024-01-15
**Version:** 1.0
