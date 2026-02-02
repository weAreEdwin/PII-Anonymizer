"""
Decrypt Router - Endpoints for reversible anonymization
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional

from ..database import get_db
from ..models import User, AnonymizationSession, AuditLog
from ..utils.security import get_current_user, verify_password
from ..services.encryption import EncryptionService
from ..schemas import DecryptRequest, DecryptResponse

router = APIRouter(prefix="/api/decrypt", tags=["decrypt"])
encryption_service = EncryptionService()

# Rate limiting storage (in-memory for simplicity, use Redis in production)
decrypt_attempts = {}


def check_rate_limit(user_id: int, session_id: str, max_attempts: int = 5, window_hours: int = 1) -> bool:
    """
    Check if user has exceeded rate limit for decrypt attempts
    
    Args:
        user_id: User identifier
        session_id: Session identifier
        max_attempts: Maximum attempts allowed
        window_hours: Time window in hours
        
    Returns:
        bool: True if within limit, False if exceeded
    """
    key = f"{user_id}:{session_id}"
    now = datetime.utcnow()
    
    if key not in decrypt_attempts:
        decrypt_attempts[key] = []
    
    # Remove old attempts outside the time window
    cutoff_time = now - timedelta(hours=window_hours)
    decrypt_attempts[key] = [
        attempt_time for attempt_time in decrypt_attempts[key]
        if attempt_time > cutoff_time
    ]
    
    # Check if limit exceeded
    if len(decrypt_attempts[key]) >= max_attempts:
        return False
    
    # Record this attempt
    decrypt_attempts[key].append(now)
    return True


@router.post("/{session_id}", response_model=DecryptResponse)
async def decrypt_document(
    session_id: str,
    decrypt_request: DecryptRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Decrypt original document (requires password verification)
    
    Args:
        session_id: Session identifier
        decrypt_request: Contains password for verification
        current_user: Authenticated user
        db: Database session
        
    Returns:
        DecryptResponse: Original decrypted document text
    """
    # Check rate limit (5 attempts per hour)
    if not check_rate_limit(current_user.id, session_id, max_attempts=5, window_hours=1):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many decrypt attempts. Please try again later."
        )
    
    # Get session from database
    session = db.query(AnonymizationSession).filter(
        AnonymizationSession.id == session_id,
        AnonymizationSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied"
        )
    
    # Verify password
    if not verify_password(decrypt_request.password, current_user.password_hash):
        # Log failed attempt
        audit_entry = AuditLog(
            user_id=current_user.id,
            session_id=session_id,
            action="DECRYPT_FAILED",
            details="Invalid password"
        )
        db.add(audit_entry)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    # Decrypt the original document
    try:
        decrypted_text = encryption_service.decrypt_text(session.document_text_encrypted)
        
        # Update last accessed timestamp
        session.last_accessed = datetime.utcnow()
        db.commit()
        
        # Log successful decryption
        audit_entry = AuditLog(
            user_id=current_user.id,
            session_id=session_id,
            action="DECRYPT_SUCCESS",
            details="Original document decrypted"
        )
        db.add(audit_entry)
        db.commit()
        
        return DecryptResponse(
            session_id=session_id,
            original_text=decrypted_text,
            decrypted_at=datetime.utcnow(),
            message="Document successfully decrypted"
        )
        
    except Exception as e:
        # Log decryption error
        audit_entry = AuditLog(
            user_id=current_user.id,
            session_id=session_id,
            action="DECRYPT_ERROR",
            details=f"Decryption failed: {str(e)}"
        )
        db.add(audit_entry)
        db.commit()
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Decryption failed: {str(e)}"
        )


@router.get("/{session_id}/can-decrypt")
async def check_decrypt_permission(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Check if user can decrypt a session (within rate limit)
    
    Args:
        session_id: Session identifier
        current_user: Authenticated user
        db: Database session
        
    Returns:
        dict: Permission status and remaining attempts
    """
    # Get session from database
    session = db.query(AnonymizationSession).filter(
        AnonymizationSession.id == session_id,
        AnonymizationSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied"
        )
    
    # Check rate limit without incrementing
    key = f"{current_user.id}:{session_id}"
    now = datetime.utcnow()
    cutoff_time = now - timedelta(hours=1)
    
    recent_attempts = []
    if key in decrypt_attempts:
        recent_attempts = [
            attempt_time for attempt_time in decrypt_attempts[key]
            if attempt_time > cutoff_time
        ]
    
    remaining_attempts = max(0, 5 - len(recent_attempts))
    can_decrypt = remaining_attempts > 0
    
    # Get last decrypt time from audit log
    last_decrypt = db.query(AuditLog).filter(
        AuditLog.user_id == current_user.id,
        AuditLog.session_id == session_id,
        AuditLog.action == "DECRYPT_SUCCESS"
    ).order_by(AuditLog.timestamp.desc()).first()
    
    return {
        "session_id": session_id,
        "can_decrypt": can_decrypt,
        "remaining_attempts": remaining_attempts,
        "max_attempts": 5,
        "window_hours": 1,
        "last_decrypt_at": last_decrypt.timestamp if last_decrypt else None,
        "message": "Ready to decrypt" if can_decrypt else "Rate limit exceeded. Try again later."
    }


@router.get("/{session_id}/audit-log")
async def get_decrypt_audit_log(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get audit log for decrypt attempts on a session
    
    Args:
        session_id: Session identifier
        current_user: Authenticated user
        db: Database session
        
    Returns:
        dict: Audit log entries
    """
    # Get session from database
    session = db.query(AnonymizationSession).filter(
        AnonymizationSession.id == session_id,
        AnonymizationSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied"
        )
    
    # Get audit log entries related to decryption
    audit_entries = db.query(AuditLog).filter(
        AuditLog.session_id == session_id,
        AuditLog.action.in_(["DECRYPT_SUCCESS", "DECRYPT_FAILED", "DECRYPT_ERROR"])
    ).order_by(AuditLog.timestamp.desc()).limit(20).all()
    
    return {
        "session_id": session_id,
        "total_entries": len(audit_entries),
        "entries": [
            {
                "id": entry.id,
                "action": entry.action,
                "timestamp": entry.timestamp,
                "details": entry.details,
                "ip_address": entry.ip_address
            }
            for entry in audit_entries
        ]
    }
