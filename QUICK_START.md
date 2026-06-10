# 🚀 QUICK START GUIDE - Automated Scanning

Panduan cepat untuk memulai automated scanning dengan email reports.

---

## ⚡ 5 MENIT SETUP

### Windows

```powershell
# 1. Run setup script
.\setup-automated-scanning.ps1

# 2. Start app (tunggu hingga setup selesai)
python -m uvicorn backend.main:app --reload
```

### Linux/Mac

```bash
# 1. Run setup script
chmod +x setup-automated-scanning.sh
./setup-automated-scanning.sh

# 2. Start app
python -m uvicorn backend.main:app --reload
```

---

## 📧 SETUP EMAIL (MANUAL)

Jika tidak pakai setup script:

### 1. Edit `.env` file

```env
# Email configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your-email@gmail.com
SENDER_PASSWORD=your-app-password

# Scheduler
ENABLE_SCHEDULER=true
SCAN_INTERVAL_HOURS=6
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Start application

```bash
python -m uvicorn backend.main:app --reload
```

---

## 👤 REGISTER USER & SET EMAIL

### 1. Register

```bash
curl -X POST "http://localhost:8000/auth/register?username=admin&password=admin123"
```

Response:
```json
{"status": "success", "token": "YOUR_TOKEN_HERE"}
```

### 2. Set Email Preferences

```bash
curl -X POST "http://localhost:8000/auth/email-settings?token=YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@gmail.com",
    "receive_reports": true
  }'
```

---

## ✅ VERIFY SETUP

### Check Scheduler Status

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

### List Reports

```bash
curl http://localhost:8000/reports/list
```

---

## 🌐 ACCESS REPORTS

### Via Browser

Open: `http://localhost:8000/reports/{scan_id}/html`

Example: `http://localhost:8000/reports/1/html`

### Via API

```bash
# List all reports
curl http://localhost:8000/reports/list

# Get report info
curl http://localhost:8000/reports/1/info

# Download HTML report
curl -O http://localhost:8000/reports/1/download
```

---

## 📋 CONFIGURATION PRESETS

### Development (Test Email Every Hour)
```env
ENABLE_SCHEDULER=true
SCAN_INTERVAL_HOURS=1
```

### Production (Every 6 Hours)
```env
ENABLE_SCHEDULER=true
SCAN_INTERVAL_HOURS=6
```

### Daily Scan
```env
ENABLE_SCHEDULER=true
SCAN_INTERVAL_HOURS=24
```

---

## 🐳 DOCKER SETUP (Optional)

```bash
# Update docker-compose.yml .env section, then:
docker-compose up -d

# Check logs
docker-compose logs -f scanner-api

# Access API
curl http://localhost:8000/scheduler/status
```

---

## 🆘 TROUBLESHOOTING

### Email tidak terkirim?
1. Check `.env` - pastikan email config benar
2. Test SMTP: Pastikan internet connection aktif
3. Check email setting: `curl http://localhost:8000/auth/email-settings?token=YOUR_TOKEN`

### Scheduler tidak jalan?
1. Check: `ENABLE_SCHEDULER=true` di `.env`
2. Verify: `curl http://localhost:8000/scheduler/status`

### Laporan HTML tidak generate?
1. Check disk space
2. Verify folder `./reports/` ada dan writable
3. Check aplikasi logs

---

## 📚 DOKUMENTASI LENGKAP

Lihat:
- `SETUP_AUTOMATED_SCANNING.md` - Setup lengkap & troubleshooting
- `IMPLEMENTASI_AUTOMATED_SCANNING.md` - Ringkasan implementasi

---

## 📞 NEED HELP?

1. Check logs
2. Read `SETUP_AUTOMATED_SCANNING.md`
3. Verify `.env` configuration
4. Test email settings manually

---

**Done! Sekarang aplikasi Anda akan:**
- ✅ Scan otomatis setiap 6 jam
- ✅ Generate laporan HTML
- ✅ Kirim email laporan
- ✅ Berjalan di background

Happy scanning! 🔒
