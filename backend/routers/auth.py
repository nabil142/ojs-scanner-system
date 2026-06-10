import hashlib
import secrets
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.database import get_db
from backend.models.user import User

router = APIRouter()


class EmailSettingsRequest(BaseModel):
    email: str
    receive_reports: bool = False


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode("utf-8")).hexdigest()


def get_user_from_token(token: str, db: Session = Depends(get_db)):
    """Get user from authentication token"""
    user = db.query(User).filter(User.token == token).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


@router.post("/register")
def register(username: str, password: str, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already taken")

    token = secrets.token_urlsafe(32)
    user = User(username=username, password=hash_password(password), token=token)
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"status": "success", "token": token}


@router.post("/login")
def login(username: str, password: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or user.password != hash_password(password):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if not user.token:
        user.token = secrets.token_urlsafe(32)
        db.commit()
        db.refresh(user)

    return {"status": "success", "token": user.token}


@router.post("/email-settings")
def update_email_settings(
    token: str,
    settings: EmailSettingsRequest,
    db: Session = Depends(get_db)
):
    """Update user email settings for receiving scan reports"""
    user = db.query(User).filter(User.token == token).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user.email = settings.email
    user.receive_reports = settings.receive_reports
    db.commit()
    db.refresh(user)
    
    return {
        "status": "success",
        "message": "Email settings updated",
        "email": user.email,
        "receive_reports": user.receive_reports
    }


@router.get("/email-settings")
def get_email_settings(token: str, db: Session = Depends(get_db)):
    """Get current user email settings"""
    user = db.query(User).filter(User.token == token).first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    return {
        "email": user.email,
        "receive_reports": user.receive_reports
    }