from sqlalchemy import Column, Integer, String, Text, Boolean
from backend.database import Base

class Scan(Base):
    __tablename__ = "scans"

    id = Column(Integer, primary_key=True)
    target = Column(String(255))
    vulnerabilities = Column(Text)
    source = Column(String(100))
    timestamp = Column(String(100))
    is_scheduled = Column(Boolean, default=False)
    html_report_path = Column(String(255), nullable=True)