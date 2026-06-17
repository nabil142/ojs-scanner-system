import threading
import time
import os
import logging
from pathlib import Path
import json
from datetime import datetime

from backend.database import SessionLocal
from backend.models.scan import Scan
from backend.services.ojs_scanner import run_ojs_sast_scan
from backend.services.llm_reasoning_service import enrich_vulnerabilities_with_reasoning
from backend.services.html_report_service import generate_html_report
from backend.services.pdf_report_service import generate_scan_pdf
from backend.services.email_service import send_report_email
from backend.models.user import User

logger = logging.getLogger(__name__)

_watcher_thread = None
_stop_event = threading.Event()

def watch_trigger_loop():
    # Detect trigger path
    trigger_path_str = os.environ.get("SCANNER_TRIGGER_PATH") or os.environ.get("OJS_SCANNER_TRIGGER_FILE") or "/scan-trigger/ojs-page-trigger.json"
    if not trigger_path_str.startswith("/") and ":" not in trigger_path_str:
        # Relative path, resolve it relative to project root
        trigger_path = Path(trigger_path_str).resolve()
    else:
        trigger_path = Path(trigger_path_str)
        
    source_path = os.environ.get("OJS_SOURCE_PATH", "ojs/ojs-main")
    
    logger.info(f"Trigger watcher thread started, watching file: {trigger_path}")
    
    last_mtime = None
    if trigger_path.exists():
        try:
            last_mtime = trigger_path.stat().st_mtime_ns
        except OSError:
            pass
        
    while not _stop_event.is_set():
        try:
            if trigger_path.exists():
                try:
                    current_mtime = trigger_path.stat().st_mtime_ns
                    if last_mtime is None:
                        last_mtime = current_mtime
                    elif current_mtime != last_mtime:
                        logger.info(f"OJS Page Trigger file changed! Running urgent scan on: {source_path}")
                        last_mtime = current_mtime
                        run_urgent_scan(source_path)
                except OSError:
                    pass
            
            # Watch every 5 seconds
            time.sleep(5)
        except Exception as e:
            logger.error(f"Error in trigger watcher loop: {e}")
            time.sleep(10)

def run_urgent_scan(source_path):
    db = SessionLocal()
    try:
        sast_scan = run_ojs_sast_scan(source_path)
        if not sast_scan.get("ok"):
            logger.error(f"Urgent scan failed: {sast_scan.get('error')}")
            return
            
        repository_status = sast_scan.get("repository_status", {})
        vulnerabilities = sast_scan.get("findings", [])
        
        # Enrich with Gemini LLM
        vulnerabilities, llm_status = enrich_vulnerabilities_with_reasoning(
            source_path,
            repository_status,
            vulnerabilities,
        )
        
        # Save record to database
        scan_record = Scan(
            target=source_path,
            vulnerabilities=json.dumps(vulnerabilities, ensure_ascii=False),
            source="PKP OJS SAST Agent (Urgent Alert Triggered)",
            timestamp=sast_scan.get("scanned_at") or datetime.utcnow().isoformat(),
            is_scheduled=False,
        )
        db.add(scan_record)
        db.commit()
        db.refresh(scan_record)
        
        logger.info(f"Urgent Scan completed. Record ID: {scan_record.id}, Vulnerabilities: {len(vulnerabilities)}")
        
        # Generate reports (HTML & PDF)
        html_path = None
        pdf_path = None
        try:
            html_path = generate_html_report(scan_record, vulnerabilities)
            scan_record.html_report_path = html_path
            
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            pdf_path = reports_dir / f"scan_report_{scan_record.id}.pdf"
            pdf_buffer = generate_scan_pdf(scan_record, vulnerabilities)
            with open(pdf_path, "wb") as f:
                f.write(pdf_buffer.getvalue())
                
            db.commit()
            logger.info(f"Reports successfully generated for urgent alert: {html_path} and {pdf_path}")
        except Exception as e:
            logger.error(f"Failed to generate reports in trigger watcher: {e}")
            
        # Get severity counts
        critical_count = sum(1 for v in vulnerabilities if str(v.get("level", "")).lower() == "critical")
        high_count = sum(1 for v in vulnerabilities if str(v.get("level", "")).lower() == "high")
        medium_count = sum(1 for v in vulnerabilities if str(v.get("level", "")).lower() == "medium")
        low_count = sum(1 for v in vulnerabilities if str(v.get("level", "")).lower() == "low")
        
        # Check if we have any high/critical issues, or if we want to send alert on any scan trigger
        # Send email alert to all users with notifications enabled
        users = db.query(User).filter(
            User.receive_reports == True,
            User.email != None,
            User.email != ""
        ).all()
        
        if users:
            logger.info(f"Sending urgent alert email notifications to {len(users)} users")
            for user in users:
                try:
                    send_report_email(
                        recipient_email=user.email,
                        scan_id=scan_record.id,
                        target=source_path,
                        html_report_path=html_path or "",
                        pdf_report_path=str(pdf_path) if pdf_path else None,
                        vulnerability_count=len(vulnerabilities),
                        critical_count=critical_count,
                        high_count=high_count,
                        medium_count=medium_count,
                        low_count=low_count,
                        is_scheduled=False,
                    )
                    logger.info(f"Urgent alert email sent successfully to {user.email}")
                except Exception as e:
                    logger.error(f"Failed to send urgent alert email to {user.email}: {e}")
                    
    except Exception as e:
        logger.error(f"Error in run_urgent_scan: {e}")
    finally:
        db.close()

def start_trigger_watcher():
    global _watcher_thread
    if _watcher_thread and _watcher_thread.is_alive():
        logger.warning("Trigger watcher is already running")
        return
        
    _stop_event.clear()
    _watcher_thread = threading.Thread(target=watch_trigger_loop, daemon=True)
    _watcher_thread.start()
    logger.info("Trigger watcher thread started successfully")

def stop_trigger_watcher():
    _stop_event.set()
    logger.info("Trigger watcher thread stop requested")
