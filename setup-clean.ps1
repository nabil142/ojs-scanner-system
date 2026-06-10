# setup-clean.ps1

# OJS Security Scanner - Automated Setup Script

Write-Host "OJS Security Scanner - Automated Scanning Setup" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

# Check Python

try {
$pythonVersion = python --version 2>&1
Write-Host "[OK] Python version: $pythonVersion" -ForegroundColor Green
}
catch {
Write-Host "[ERROR] Python not found. Please install Python first." -ForegroundColor Red
exit 1
}

Write-Host ""

# =========================

# SMTP CONFIGURATION

# =========================

Write-Host "Email Configuration (SMTP)" -ForegroundColor Yellow
Write-Host "--------------------------"

$smtpServer = Read-Host "SMTP Server (default: smtp.gmail.com)"
if ([string]::IsNullOrWhiteSpace($smtpServer)) {
$smtpServer = "smtp.gmail.com"
}

$smtpPort = Read-Host "SMTP Port (default: 587)"
if ([string]::IsNullOrWhiteSpace($smtpPort)) {
$smtpPort = "587"
}

$senderEmail = Read-Host "Sender Email Address"

$senderPassword = Read-Host "Sender Email App Password" -AsSecureString
$senderPasswordPlain = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
[Runtime.InteropServices.Marshal]::SecureStringToCoTaskMemUnicode($senderPassword)
)

$reportRecipient = Read-Host "Report Recipient Email"

Write-Host ""

# =========================

# SCHEDULER CONFIGURATION

# =========================

Write-Host "Scheduler Configuration" -ForegroundColor Yellow
Write-Host "-----------------------"

$scanInterval = Read-Host "Scan Interval (hours, default: 6)"
if ([string]::IsNullOrWhiteSpace($scanInterval)) {
$scanInterval = "6"
}

$enableScheduler = Read-Host "Enable Scheduler? (true/false, default: true)"
if ([string]::IsNullOrWhiteSpace($enableScheduler)) {
$enableScheduler = "true"
}

Write-Host ""

# =========================

# OJS CONFIGURATION

# =========================

$ojsSourcePath = Read-Host "OJS Source Path (default: ojs/ojs-main)"
if ([string]::IsNullOrWhiteSpace($ojsSourcePath)) {
$ojsSourcePath = "ojs/ojs-main"
}

Write-Host ""

# =========================

# CREATE .ENV

# =========================

Write-Host "Generating .env file..." -ForegroundColor Green

$envContent = @"

# ==========================================

# OJS SECURITY SCANNER CONFIGURATION

# ==========================================

# LLM Configuration

LLM_PROVIDER=openai
LLM_API_KEY=
LLM_MODEL=gpt-4o-mini
LLM_TIMEOUT=30

# Scanner Configuration

OJS_SOURCE_PATH=$ojsSourcePath
SCANNER_OUTPUT_PATH=scan-output/latest.json
SEMGREP_ENABLED=true
SEMGREP_TIMEOUT_SECONDS=90

# Scheduler

ENABLE_SCHEDULER=$enableScheduler
SCAN_INTERVAL_HOURS=$scanInterval

# SMTP Configuration

SMTP_SERVER=$smtpServer
SMTP_PORT=$smtpPort
SMTP_USERNAME=$senderEmail
SMTP_PASSWORD=$senderPasswordPlain

# Report Recipient

REPORT_RECIPIENT=$reportRecipient
"@

Set-Content -Path ".env" -Value $envContent -Encoding UTF8

Write-Host "[OK] .env file created successfully" -ForegroundColor Green
Write-Host ""

# =========================

# INSTALL DEPENDENCIES

# =========================

if (Test-Path "requirements.txt") {
Write-Host "Installing dependencies..." -ForegroundColor Green
pip install -r requirements.txt

```
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Dependencies installed" -ForegroundColor Green
}
else {
    Write-Host "[WARNING] Dependency installation returned an error" -ForegroundColor Yellow
}
```

}
else {
Write-Host "[WARNING] requirements.txt not found" -ForegroundColor Yellow
}

Write-Host ""

# =========================

# DATABASE INITIALIZATION

# =========================

if (Test-Path "backend") {
Write-Host "Initializing database..." -ForegroundColor Green

```
try {
    python -c "from backend.database import engine, Base; Base.metadata.create_all(bind=engine); print('Database initialized')"

    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Database initialized" -ForegroundColor Green
    }
}
catch {
    Write-Host "[WARNING] Database initialization skipped" -ForegroundColor Yellow
}
```

}
else {
Write-Host "[WARNING] backend folder not found, skipping database initialization" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host ""

Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "--------------------------------"
Write-Host "1. Add your OpenAI API key to .env"
Write-Host ""
Write-Host "2. Start the backend:"
Write-Host "   python -m uvicorn backend.main:app --reload"
Write-Host ""
Write-Host "3. Register a user:"
Write-Host "   curl -X POST 'http://localhost:8000/auth/register?username=admin&password=admin123'"
Write-Host ""
Write-Host "4. Check scheduler status:"
Write-Host "   curl 'http://localhost:8000/scheduler/status'"
Write-Host ""
Write-Host "5. Verify email configuration and run a test scan"
Write-Host ""
Write-Host "Documentation: SETUP_AUTOMATED_SCANNING.md" -ForegroundColor Cyan
