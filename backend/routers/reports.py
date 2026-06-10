from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os
import json
from pathlib import Path

from backend.database import get_db
from backend.models.scan import Scan

router = APIRouter()


@router.get("/list")
def list_reports(db: Session = Depends(get_db)):
    """List all available scan reports"""
    try:
        scans = db.query(Scan).order_by(Scan.timestamp.desc()).all()
        
        reports = []
        for scan in scans:
            report_info = {
                "id": scan.id,
                "target": scan.target,
                "timestamp": scan.timestamp,
                "source": scan.source,
                "is_scheduled": scan.is_scheduled,
                "html_report_available": bool(scan.html_report_path and Path(scan.html_report_path).exists()),
                "html_report_path": scan.html_report_path,
            }
            reports.append(report_info)
        
        return {
            "status": "success",
            "total": len(reports),
            "reports": reports
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing reports: {str(e)}")


@router.get("/{scan_id}/html")
def get_html_report(scan_id: int, db: Session = Depends(get_db)):
    """Get HTML report for a specific scan"""
    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        if not scan.html_report_path:
            raise HTTPException(status_code=404, detail="HTML report not available for this scan")
        
        report_path = Path(scan.html_report_path)
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Report file not found")
        
        return FileResponse(
            path=report_path,
            filename=report_path.name,
            media_type="text/html"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving report: {str(e)}")


@router.get("/{scan_id}/info")
def get_report_info(scan_id: int, db: Session = Depends(get_db)):
    """Get information about a specific scan"""
    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        import json
        vulnerabilities = json.loads(scan.vulnerabilities) if scan.vulnerabilities else []
        
        severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        for vuln in vulnerabilities:
            level = str(vuln.get("level", "Low")).capitalize()
            if level not in severity_counts:
                severity_counts[level] = 0
            severity_counts[level] += 1
        
        return {
            "id": scan.id,
            "target": scan.target,
            "timestamp": scan.timestamp,
            "source": scan.source,
            "is_scheduled": scan.is_scheduled,
            "total_vulnerabilities": len(vulnerabilities),
            "severity_counts": severity_counts,
            "html_report_available": bool(scan.html_report_path and Path(scan.html_report_path).exists()),
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving report info: {str(e)}")


@router.get("/{scan_id}/download")
def download_html_report(scan_id: int, db: Session = Depends(get_db)):
    """Download HTML report as attachment"""
    try:
        scan = db.query(Scan).filter(Scan.id == scan_id).first()
        if not scan:
            raise HTTPException(status_code=404, detail="Scan not found")
        
        if not scan.html_report_path:
            raise HTTPException(status_code=404, detail="HTML report not available")
        
        report_path = Path(scan.html_report_path)
        if not report_path.exists():
            raise HTTPException(status_code=404, detail="Report file not found")
        
        return FileResponse(
            path=report_path,
            filename=f"ojs_security_report_{scan_id}.html",
            media_type="text/html"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error downloading report: {str(e)}")
