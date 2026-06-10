from sqlalchemy import Column, Integer, String, Boolean
from backend.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True)
    password = Column(String(128))
    token = Column(String(255), nullable=True)
    email = Column(String(255), nullable=True)
    receive_reports = Column(Boolean, default=False)