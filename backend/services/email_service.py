import logging
import os
import smtplib

from pathlib import Path

from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication

logger = logging.getLogger(__name__)


import base64
import requests


def send_email_via_brevo(
    api_key: str,
    sender_email: str,
    recipient_email: str,
    scan_id: int,
    target: str,
    html_report_path: str,
    pdf_report_path: str | None,
    vulnerability_count: int,
    critical_count: int,
    high_count: int,
    medium_count: int,
    low_count: int,
    is_scheduled: bool,
):
    try:
        logger.info(f"Sending email via Brevo HTTPS API to {recipient_email}")
        
        # Parse sender name and clean email
        clean_sender_email = sender_email.strip()
        sender_name = "OJS Scanner"
        if "<" in sender_email and ">" in sender_email:
            parts = sender_email.split("<")
            possible_name = parts[0].strip()
            if possible_name:
                sender_name = possible_name.strip('"\' ')
            clean_sender_email = parts[1].split(">")[0].strip()
            
        # Fix potential typos (like double @@)
        if "@@" in clean_sender_email:
            clean_sender_email = clean_sender_email.replace("@@", "@")
            
        logger.info(f"Parsed sender for Brevo: name='{sender_name}', email='{clean_sender_email}'")
        
        # Build subject
        scan_type = "SCHEDULED" if is_scheduled else "MANUAL"
        subject = f"[{scan_type}] [C:{critical_count}][H:{high_count}][M:{medium_count}][L:{low_count}] OJS Security Report #{scan_id}"
        
        # Build HTML body
        from datetime import datetime
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Asia/Jakarta"))
        scan_type_text = "Scheduled Scan" if is_scheduled else "Manual Scan"
        
        html_body = f"""
        <html>
        <body style="font-family:Arial,sans-serif;">
        <h2>OJS Security Scan Notification (via Brevo)</h2>
        <p>Berikut hasil report keamanan OJS yang telah selesai dijalankan.</p>
        <table cellpadding="6">
        <tr><td><b>Jenis Scan</b></td><td>{scan_type_text}</td></tr>
        <tr><td><b>Tanggal</b></td><td>{now.strftime("%d %B %Y")}</td></tr>
        <tr><td><b>Waktu</b></td><td>{now.strftime("%H:%M:%S WIB")}</td></tr>
        <tr><td><b>Target</b></td><td>{target}</td></tr>
        </table>
        <br>
        <h3>Severity Summary</h3>
        <ul>
        <li>Critical : {critical_count}</li>
        <li>High : {high_count}</li>
        <li>Medium : {medium_count}</li>
        <li>Low : {low_count}</li>
        <li>Total : {vulnerability_count}</li>
        </ul>
        <p>Laporan lengkap tersedia pada lampiran.</p>
        <p>Regards,<br>OJS Security Scanner</p>
        </body>
        </html>
        """

        headers = {
            "api-key": api_key,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        payload = {
            "sender": {"name": sender_name, "email": clean_sender_email},
            "to": [{"email": recipient_email}],
            "subject": subject,
            "htmlContent": html_body,
            "attachment": []
        }
        
        # Attach PDF
        if pdf_report_path and Path(pdf_report_path).exists():
            with open(pdf_report_path, "rb") as f:
                pdf_data = f.read()
                payload["attachment"].append({
                    "content": base64.b64encode(pdf_data).decode("utf-8"),
                    "name": Path(pdf_report_path).name
                })
                logger.info(f"Brevo attached PDF: {pdf_report_path}")

        # Attach HTML
        if html_report_path and Path(html_report_path).exists():
            with open(html_report_path, "rb") as f:
                html_data = f.read()
                payload["attachment"].append({
                    "content": base64.b64encode(html_data).decode("utf-8"),
                    "name": Path(html_report_path).name
                })
                logger.info(f"Brevo attached HTML: {html_report_path}")

        response = requests.post("https://api.brevo.com/v3/smtp/email", json=payload, headers=headers, timeout=15)
        
        if response.status_code in (200, 201, 202):
            logger.info(f"Email report sent successfully via Brevo to {recipient_email}")
            return True
        else:
            logger.error(f"Brevo API error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Failed to send email via Brevo to {recipient_email}: {e}")
        return False


def send_report_email(
    recipient_email: str,
    scan_id: int,
    target: str,
    html_report_path: str,
    pdf_report_path: str | None = None,
    vulnerability_count: int = 0,
    critical_count: int = 0,
    high_count: int = 0,
    medium_count: int = 0,
    low_count: int = 0,
    is_scheduled: bool = False,
):
    """
    Send scan report email.
    """

    brevo_api_key = os.environ.get("BREVO_API_KEY")
    if brevo_api_key:
        sender_email = (
            os.environ.get("SENDER_EMAIL")
            or os.environ.get("SMTP_USERNAME")
            or "nabilathaya2005@gmail.com"
        )
        return send_email_via_brevo(
            api_key=brevo_api_key,
            sender_email=sender_email,
            recipient_email=recipient_email,
            scan_id=scan_id,
            target=target,
            html_report_path=html_report_path,
            pdf_report_path=pdf_report_path,
            vulnerability_count=vulnerability_count,
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
            is_scheduled=is_scheduled,
        )

    smtp_server = os.environ.get("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))

    sender_email = (
        os.environ.get("SENDER_EMAIL")
        or os.environ.get("SMTP_USERNAME")
        or ""
    )

    sender_password = (
        os.environ.get("SENDER_PASSWORD")
        or os.environ.get("SMTP_PASSWORD")
        or ""
    )

    if not sender_email or not sender_password:
        logger.warning("Email not configured. Skipping email notification.")
        return False

    try:
        logger.info(
            f"Sending security report email to {recipient_email}"
        )

        # HTML body
        from datetime import datetime
        from zoneinfo import ZoneInfo
        now = datetime.now(
            ZoneInfo("Asia/Jakarta")
)
        scan_type_text = (
            "Scheduled Scan"
            if is_scheduled
            else "Manual Scan"
            )
        html_body = f"""
        <html>
        <body style="font-family:Arial,sans-serif;">
        <h2>OJS Security Scan Notification</h2>
        <p>
        Berikut hasil report keamanan OJS yang telah selesai dijalankan.
        </p>

        <table cellpadding="6">
        <tr>
        <td><b>Jenis Scan</b></td>
        <td>{scan_type_text}</td>
        </tr>

        <tr>
        <td><b>Tanggal</b></td>
        <td>{now.strftime("%d %B %Y")}</td>
        </tr>

        <tr>
        <td><b>Waktu</b></td>
        <td>{now.strftime("%H:%M:%S WIB")}</td>
        </tr>

        <tr>
        <td><b>Target</b></td>
        <td>{target}</td>
        </tr>
        </table>

        <br>

        <h3>Severity Summary</h3>

        <ul>
        <li>Critical : {critical_count}</li>
        <li>High : {high_count}</li>
        <li>Medium : {medium_count}</li>
        <li>Low : {low_count}</li>
        <li>Total : {vulnerability_count}</li>
        </ul>

        <p>
        Laporan lengkap tersedia pada lampiran:
        </p>

        <ul>
        <li>HTML Report</li>
        <li>PDF Report</li>
        </ul>

        <p>
        Regards,<br>
        OJS Security Scanner
        </p>

        </body>
        </html>
        """
        


        # Email container
        message = MIMEMultipart("mixed")

        scan_type = (
            "SCHEDULED"
            if is_scheduled
            else "MANUAL"
        )

        message["Subject"] = (
            f"[{scan_type}] "
            f"[C:{critical_count}]"
            f"[H:{high_count}]"
            f"[M:{medium_count}]"
            f"[L:{low_count}] "
            f"OJS Security Report #{scan_id}"
        )

        message["From"] = sender_email
        message["To"] = recipient_email

        # Plain text
        text_body = generate_plain_text_email(
            scan_id=scan_id,
            target=target,
            vulnerability_count=vulnerability_count,
            critical_count=critical_count,
            high_count=high_count,
            medium_count=medium_count,
            low_count=low_count,
        )

        alternative_part = MIMEMultipart("alternative")

        alternative_part.attach(
            MIMEText(text_body, "plain")
        )

        alternative_part.attach(
            MIMEText(html_body, "html")
        )

        message.attach(alternative_part)
        # Attach PDF report
        
        if (
            pdf_report_path
            and Path(pdf_report_path).exists()
):
            with open(pdf_report_path, "rb") as f:
                pdf_attachment = MIMEApplication(
                    f.read(),
                    Name=Path(pdf_report_path).name,
        )
                pdf_attachment["Content-Disposition"] = (
                    f'attachment; filename="{Path(pdf_report_path).name}"'
    )
                message.attach(pdf_attachment)
                logger.info(
                    f"Attached PDF report: {pdf_report_path}"
    )

        # Attach HTML report
        if (
            html_report_path
            and Path(html_report_path).exists()
        ):
            with open(html_report_path, "rb") as f:

                attachment = MIMEApplication(
                    f.read(),
                    Name=Path(html_report_path).name,
                )

            attachment["Content-Disposition"] = (
                f'attachment; filename="{Path(html_report_path).name}"'
            )

            message.attach(attachment)

            logger.info(
                f"Attached HTML report: {html_report_path}"
            )

        # SMTP Send
        with smtplib.SMTP(
            smtp_server,
            smtp_port
        ) as server:

            server.starttls()

            server.login(
                sender_email,
                sender_password,
            )

            server.sendmail(
                sender_email,
                recipient_email,
                message.as_string(),
            )

        logger.info(
            f"Email report sent successfully to "
            f"{recipient_email}"
        )

        return True

    except Exception as e:

        logger.error(
            f"Failed to send email report to "
            f"{recipient_email}: {e}"
        )

    return False


def generate_plain_text_email(
    scan_id,
    target,
    vulnerability_count,
    critical_count,
    high_count,
    medium_count,
    low_count,
):
    return f"""
OJS Security Scan Report
================================

Scan ID: {scan_id}
Target: {target}

VULNERABILITY SUMMARY

Total Vulnerabilities : {vulnerability_count}
Critical              : {critical_count}
High                  : {high_count}
Medium                : {medium_count}
Low                   : {low_count}

Please see the attached HTML report for full details.

---
Generated automatically by OJS Security Scanner.
"""


def generate_fallback_email_body(
    scan_id,
    target,
    total_vulns,
    critical,
    high,
    medium,
    low,
    is_scheduled=False,
):

    scan_badge = (
        """
        <div style="
        background:#16a34a;
        color:white;
        padding:8px 16px;
        display:inline-block;
        border-radius:20px;
        font-weight:bold;
        margin-bottom:15px;
        ">
        ⏰ SCHEDULED SCAN
        </div>
        """
        if is_scheduled
        else
        """
        <div style="
        background:#2563eb;
        color:white;
        padding:8px 16px;
        display:inline-block;
        border-radius:20px;
        font-weight:bold;
        margin-bottom:15px;
        ">
        👤 MANUAL SCAN
        </div>
        """
    )

    return f"""
<html>
<head>
<style>
body {{
    font-family: Arial, sans-serif;
    color: #333;
}}

.header {{
    background-color: #667eea;
    color: white;
    padding: 20px;
    border-radius: 5px;
}}

.summary {{
    background-color: #f5f5f5;
    padding: 15px;
    border-radius: 5px;
    margin-top: 20px;
}}

.severity {{
    display:inline-block;
    margin-right:10px;
    padding:8px 12px;
    border-radius:4px;
    color:white;
}}

.critical {{
    background:#dc2626;
}}

.high {{
    background:#ea580c;
}}

.medium {{
    background:#f59e0b;
}}

.low {{
    background:#2563eb;
}}
</style>
</head>

<body>

<div class="header">
{scan_badge}
<h2>OJS Security Scan Report</h2>
</div>

<div class="summary">

<p><strong>Scan ID:</strong> {scan_id}</p>
<p><strong>Target:</strong> {target}</p>
<p><strong>Total Vulnerabilities:</strong> {total_vulns}</p>

<span class="severity critical">
Critical: {critical}
</span>

<span class="severity high">
High: {high}
</span>

<span class="severity medium">
Medium: {medium}
</span>

<span class="severity low">
Low: {low}
</span>

</div>

<p>
Please see the attached HTML report for complete details.
</p>

</body>
</html>
"""