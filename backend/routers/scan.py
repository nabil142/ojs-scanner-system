from datetime import datetime
import json
import os
from typing import Optional

from fastapi import APIRouter, Body, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models.scan import Scan
from backend.services.llm_reasoning_service import enrich_vulnerabilities_with_reasoning
from backend.services.ojs_scanner import run_ojs_sast_scan, get_target_metadata
from backend.services.pdf_report_service import generate_scan_pdf
from backend.services.email_service import send_report_email
from backend.models.user import User
from pathlib import Path
from backend.services.html_report_service import generate_html_report
from backend.services.scheduler_service import get_scheduler_status



router = APIRouter()

@router.get("/scheduler/status")
def scheduler_status():
    return get_scheduler_status()

@router.get("/target-info")
def get_scan_target_info(source_path: Optional[str] = None):
    path = source_path or _default_source_path()
    try:
        return get_target_metadata(path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class ScanRequest(BaseModel):
    internal_path: Optional[str] = None


def _default_source_path():
    return os.environ.get("OJS_SOURCE_PATH", "ojs/ojs-main")


def send_email_reports_task(
    scan_record_id: int,
    target: str,
    html_report_path: str,
    pdf_report_path: Optional[str],
    vulnerabilities: list
):
    from backend.database import SessionLocal
    db = SessionLocal()
    try:
        users = db.query(User).filter(
            User.receive_reports == True,
            User.email.isnot(None)
        ).all()
        if not users:
            return

        critical_count = sum(
            1 for v in vulnerabilities
            if str(v.get("severity", "")).lower() == "critical"
        )
        high_count = sum(
            1 for v in vulnerabilities
            if str(v.get("severity", "")).lower() == "high"
        )
        medium_count = sum(
            1 for v in vulnerabilities
            if str(v.get("severity", "")).lower() == "medium"
        )
        low_count = sum(
            1 for v in vulnerabilities
            if str(v.get("severity", "")).lower() == "low"
        )

        for user in users:
            success = send_report_email(
                recipient_email=user.email,
                scan_id=scan_record_id,
                target=target,
                html_report_path=html_report_path,
                pdf_report_path=pdf_report_path,
                vulnerability_count=len(vulnerabilities),
                critical_count=critical_count,
                high_count=high_count,
                medium_count=medium_count,
                low_count=low_count,
                is_scheduled=False,
            )
            if success:
                print(f"Background email report sent to {user.email}")
            else:
                print(f"Failed sending background email to {user.email}")
    except Exception as e:
        print(f"Background email task error: {e}")
    finally:
        db.close()


@router.post("/")
def scan_target(
    payload: Optional[ScanRequest] = Body(None),
    db: Session = Depends(get_db),
    background_tasks: BackgroundTasks = None
):
    source_path = ""
    target_label = ""
    if payload:
        source_path = (payload.internal_path or "").strip()

    source_path = source_path or _default_source_path()
    target_label = source_path

    sast_scan = run_ojs_sast_scan(source_path)
    repository_status = sast_scan.get("repository_status", {
        "ok": False,
        "is_ojs": False,
        "status": "PKP OJS source detection failed",
        "message": sast_scan.get("error", ""),
    })

    if not sast_scan.get("ok"):
        return {
            "target": target_label,
            "target_valid": False,
            "repository_status": repository_status,
            "message": sast_scan.get("error", "SAST agent gagal menjalankan scan."),
            "agent_mode": "sast_only",
            "total_vulnerabilities": 0,
            "vulnerabilities": [],
            "scanner_status": {
                "agent": {
                    "ok": False,
                    "mode": "sast_only",
                    "source_path": source_path,
                    "error": sast_scan.get("error", ""),
                }
            },
            "history_id": None,
            "scanned_at": datetime.utcnow().isoformat(),
        }

    vulnerabilities = sast_scan.get("findings", [])
    vulnerabilities, llm_status = enrich_vulnerabilities_with_reasoning(
        target_label,
        repository_status,
        vulnerabilities,
    )

    scan_record = Scan(
        target=target_label,
        vulnerabilities=json.dumps(vulnerabilities, ensure_ascii=False),
        source="PKP OJS SAST Agent",
        timestamp=sast_scan.get("scanned_at") or datetime.utcnow().isoformat(),
    )
    db.add(scan_record)
    db.commit()
    db.refresh(scan_record)
    
    # Generate HTML report
    html_report_path = None
    pdf_report_path = None

    # Generate HTML report
    try:
        html_report_path = generate_html_report(
        scan_record,
        vulnerabilities
)

        scan_record.html_report_path = html_report_path

        reports_dir = Path("reports")
        reports_dir.mkdir(exist_ok=True)

        pdf_report_path = (
            reports_dir
            / f"scan_report_{scan_record.id}.pdf"
)
        pdf_buffer = generate_scan_pdf(
            scan_record,
            vulnerabilities
)
        with open(pdf_report_path, "wb") as f:
            f.write(pdf_buffer.getvalue())
            db.commit()

    except Exception as e:
        print(f"Error generating HTML report: {e}")

    # Send email notifications in background
    if html_report_path and background_tasks:
        background_tasks.add_task(
            send_email_reports_task,
            scan_record.id,
            scan_record.target,
            html_report_path,
            str(pdf_report_path) if pdf_report_path else None,
            vulnerabilities
        )
    

    return {
        "target": target_label,
        "target_valid": bool(repository_status.get("is_ojs")),
        "repository_status": repository_status,
        "message": "Scan SAST agent selesai.",
        "agent_mode": "sast_only",
        "internal_scan": {
            "ok": sast_scan.get("ok", False),
            "enabled": sast_scan.get("enabled", False),
            "error": sast_scan.get("error", ""),
            "metadata": sast_scan.get("metadata", {}),
        },
        "total_vulnerabilities": len(vulnerabilities),
        "vulnerabilities": vulnerabilities,
        "scanner_status": {
            "agent": {
                "ok": sast_scan.get("ok", False),
                "mode": "sast_only",
                "source_path": source_path,
                "error": sast_scan.get("error", ""),
                "metadata": sast_scan.get("metadata", {}),
            },
            "llm_reasoning": llm_status,
        },
        "llm_reasoning": llm_status,
        "history_id": scan_record.id,
        "html_report_url": f"/reports/{scan_record.id}/html",
        "scanned_at": scan_record.timestamp,
    }


@router.get("/history")
def scan_history(db: Session = Depends(get_db)):
    scans = db.query(Scan).order_by(Scan.id.desc()).limit(50).all()
    return [
        {
            "id": item.id,
            "target": item.target,
            "timestamp": item.timestamp,
            "source": item.source,
            "vulnerabilities": json.loads(item.vulnerabilities or "[]"),
        }
        for item in scans
    ]


@router.get("/report/{scan_id}")
def download_scan_report(scan_id: int, db: Session = Depends(get_db)):
    scan_record = db.query(Scan).filter(Scan.id == scan_id).first()
    if not scan_record:
        raise HTTPException(status_code=404, detail="Scan history not found")

    try:
        vulnerabilities = json.loads(scan_record.vulnerabilities or "[]")
    except json.JSONDecodeError:
        vulnerabilities = []

    try:
        pdf_buffer = generate_scan_pdf(scan_record, vulnerabilities)
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc))

    filename = f"ojs-security-report-{scan_record.id}.pdf"
    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
