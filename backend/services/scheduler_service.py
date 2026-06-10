import logging
import json
from datetime import datetime
from typing import Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.orm import Session

from backend.database import SessionLocal
from backend.models.scan import Scan
from backend.models.user import User
from backend.services.ojs_scanner import run_ojs_sast_scan
from backend.services.llm_reasoning_service import enrich_vulnerabilities_with_reasoning
from backend.services.html_report_service import generate_html_report
from backend.services.email_service import send_report_email
from datetime import datetime

logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()


def run_scheduled_scan(source_path: str = None):
    """Execute a scheduled scan"""
    import os
    
    if source_path is None:
        source_path = os.environ.get("OJS_SOURCE_PATH", "ojs/ojs-main")
    
    db = SessionLocal()
    
    try:
        logger.info(f"Starting scheduled scan for: {source_path}")
        
        # Run SAST scan
        sast_scan = run_ojs_sast_scan(source_path)
        repository_status = sast_scan.get("repository_status", {
            "ok": False,
            "is_ojs": False,
            "status": "PKP OJS source detection failed",
            "message": sast_scan.get("error", ""),
        })
        
        if not sast_scan.get("ok"):
            logger.error(f"Scan failed: {sast_scan.get('error')}")
            return False
        
        # Extract vulnerabilities
        vulnerabilities = sast_scan.get("findings", [])
        vulnerabilities, llm_status = enrich_vulnerabilities_with_reasoning(
            source_path,
            repository_status,
            vulnerabilities,
        )
        
        # Create scan record
        scan_record = Scan(
            target=source_path,
            vulnerabilities=json.dumps(vulnerabilities, ensure_ascii=False),
            source="PKP OJS SAST Agent (Scheduled)",
            timestamp=sast_scan.get("scanned_at") or datetime.utcnow().isoformat(),
            is_scheduled=True,
        )
        db.add(scan_record)
        db.commit()
        db.refresh(scan_record)
        
        logger.info(f"Scan completed. Record ID: {scan_record.id}, Vulnerabilities: {len(vulnerabilities)}")
        
        # Generate HTML report
        try:
            html_report_path = generate_html_report(scan_record, vulnerabilities)
            scan_record.html_report_path = html_report_path
            db.commit()
            logger.info(f"HTML report generated: {html_report_path}")
        except Exception as e:
            logger.error(f"Failed to generate HTML report: {str(e)}")
        
        # Get severity counts for email
        severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for vuln in vulnerabilities:
            level = str(vuln.get("level", "Low")).capitalize()
            if level not in severity_counts:
                severity_counts[level] = 0
            severity_counts[level] += 1
        
        # Send reports to users
        send_scheduled_reports(
            db,
            scan_record,
            len(vulnerabilities),
            severity_counts.get("Critical", 0),
            severity_counts.get("High", 0),
            severity_counts.get("Medium", 0),
            severity_counts.get("Low", 0),
        )
        
        return True
        
    except Exception as e:
        logger.error(f"Error during scheduled scan: {str(e)}", exc_info=True)
        return False
    finally:
        db.close()


def send_scheduled_reports(
    db: Session,
    scan_record: Scan,
    total_vulns: int,
    critical: int,
    high: int,
    medium: int,
    low: int,
):
    """Send scan reports to all users with email notifications enabled"""
    
    try:
        # Get all users with email notifications enabled
        users = db.query(User).filter(
            User.receive_reports == True,
            User.email != None,
            User.email != ""
        ).all()
        
        if not users:
            logger.info("No users configured to receive scan reports")
            return
        
        logger.info(f"Sending reports to {len(users)} users")
        
        for user in users:
            try:
                send_report_email(
                    recipient_email=user.email,
                    scan_id=scan_record.id,
                    target=scan_record.target,
                    html_report_path=scan_record.html_report_path or "",
                    vulnerability_count=total_vulns,
                    critical_count=critical,
                    high_count=high,
                    medium_count=medium,
                    low_count=low,
                )
                logger.info(f"Report sent to {user.email}")
            except Exception as e:
                logger.error(f"Failed to send report to {user.email}: {str(e)}")
        
    except Exception as e:
        logger.error(f"Error sending reports: {str(e)}", exc_info=True)


def start_scheduler(interval_hours: int = 1, source_path: Optional[str] = None):
    """Start the background scheduler"""

    if scheduler.running:
        logger.warning("Scheduler is already running")
        return

    try:
        scheduler.add_job(
            func=run_scheduled_scan,
            kwargs={"source_path": source_path},
            trigger=IntervalTrigger(hours=interval_hours),
            id="scheduled_scan",
            name="Scheduled OJS Security Scan",
            replace_existing=True,
            coalesce=True,
            max_instances=1,
        )

        scheduler.start()

        logger.info(
            f"Scheduler started - scans will run every {interval_hours} hours"
        )

        job = scheduler.get_job("scheduled_scan")

        if job:
            logger.info(
                f"Next scheduled scan at: {job.next_run_time}"
            )

    except Exception as e:
        logger.error(
            f"Failed to start scheduler: {str(e)}",
            exc_info=True
        )


def stop_scheduler():
    """Stop the background scheduler"""
    
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler stopped")


def get_scheduler_status():
    jobs = []

    for job in scheduler.get_jobs():

        remaining_seconds = None

        if job.next_run_time:
            remaining_seconds = int(
                (
                    job.next_run_time
                    - datetime.now(job.next_run_time.tzinfo)
                ).total_seconds()
            )

        jobs.append({
            "id": job.id,
            "name": job.name,
            "trigger": str(job.trigger),
            "next_run_time": (
                job.next_run_time.isoformat()
                if job.next_run_time
                else None
            ),
            "remaining_seconds": remaining_seconds,
            "remaining_minutes": (
                round(remaining_seconds / 60, 2)
                if remaining_seconds
                else None
            ),
        })

    return {
        "running": scheduler.running,
        "jobs": jobs,
    }
