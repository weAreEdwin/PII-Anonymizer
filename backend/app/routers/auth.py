from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from ..database import get_db
from ..schemas import UserCreate, UserLogin, Token, UserResponse
from ..models import User, AuditLog
from ..utils.security import (
    get_password_hash,
    authenticate_user,
    create_access_token,
    get_current_user
)
from ..config import settings

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    # Check if username already exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Log registration
    audit_entry = AuditLog(
        user_id=new_user.id,
        action="USER_REGISTERED",
        ip_address=None  # Will be populated from request in production
    )
    db.add(audit_entry)
    db.commit()
    
    return new_user


@router.post("/login", response_model=Token)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """Login and get access token"""
    user = authenticate_user(db, user_credentials.username, user_credentials.password)
    
    if not user:
        # Log failed login attempt
        db_user = db.query(User).filter(User.username == user_credentials.username).first()
        if db_user:
            audit_entry = AuditLog(
                user_id=db_user.id,
                action="LOGIN_FAILED",
                ip_address=None
            )
            db.add(audit_entry)
            db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )
    
    # Log successful login
    audit_entry = AuditLog(
        user_id=user.id,
        action="LOGIN_SUCCESS",
        ip_address=None
    )
    db.add(audit_entry)
    db.commit()
    
    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Logout user (client-side token deletion)"""
    # Log logout
    audit_entry = AuditLog(
        user_id=current_user.id,
        action="USER_LOGOUT",
        ip_address=None
    )
    db.add(audit_entry)
    db.commit()
    
    return {"message": "Successfully logged out"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user
