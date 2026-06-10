from fastapi import FastAPI
from backend.routers import scan, auth, reports
from fastapi.middleware.cors import CORSMiddleware
import os
import logging

app = FastAPI(title="OJS Security Scanner")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # untuk demo (bebas)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router, prefix="/scan", tags=["Scan"])
app.include_router(auth.router, prefix="/auth", tags=["Auth"])
app.include_router(reports.router, prefix="/reports", tags=["Reports"])

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.on_event("startup")
def startup():
    from backend.database import engine, Base
    Base.metadata.create_all(bind=engine)
    
    # Start scheduler for automated scanning
    from backend.services.scheduler_service import start_scheduler
    
    # Get configuration from environment
    scan_interval_hours = int(os.environ.get("SCAN_INTERVAL_HOURS", "6"))
    ojs_source_path = os.environ.get("OJS_SOURCE_PATH", "ojs/ojs-main")
    enable_scheduler = os.environ.get("ENABLE_SCHEDULER", "true").lower() == "true"
    
    if enable_scheduler:
        logger.info(f"Starting scheduler with {scan_interval_hours} hours interval")
        start_scheduler(interval_hours=scan_interval_hours, source_path=ojs_source_path)
    else:
        logger.info("Scheduler is disabled")


@app.on_event("shutdown")
def shutdown():
    from backend.services.scheduler_service import stop_scheduler
    logger.info("Shutting down scheduler")
    stop_scheduler()


@app.get("/")
def root():
    return {"message": "OJS Security Scanner API"}


@app.get("/scheduler/status")
def get_scheduler_status():
    """Get current scheduler status"""
    from backend.services.scheduler_service import get_scheduler_status
    return get_scheduler_status()