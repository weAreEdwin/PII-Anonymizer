from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
import uuid
import json

from ..database import get_db
from ..models import User, AnonymizationSession, PIIMapping, AuditLog
from ..utils.security import get_current_user
from ..services.file_processor import FileProcessor
from ..services.pii_detector import PIIDetector
from ..services.anonymizer import Anonymizer
from ..services.encryption import encryption_service
from ..schemas import SessionResponse, SessionDetailResponse

router = APIRouter(prefix="/api", tags=["Document Processing"])

# Initialize services
file_processor = FileProcessor()
pii_detector = PIIDetector()


@router.post("/upload", response_model=SessionResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process a document for PII anonymization
    
    Steps:
    1. Validate and extract text from file
    2. Detect PII using spaCy + regex
    3. Anonymize text with placeholders
    4. Encrypt and store in database
    5. Return session ID and preview
    """
    
    # Step 1: Extract text from file
    try:
        document_text, file_type = await file_processor.extract_text(file)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process file: {str(e)}"
        )
    
    if not document_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No text content found in document"
        )
    
    # Step 2: Detect PII
    try:
        entities = pii_detector.detect_pii(document_text)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"PII detection failed: {str(e)}"
        )
    
    # Step 3: Anonymize text
    anonymizer = Anonymizer()
    try:
        anonymized_text, pii_mapping = anonymizer.anonymize_text(document_text, entities)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Anonymization failed: {str(e)}"
        )
    
    # Step 4: Encrypt sensitive data
    try:
        encrypted_original = encryption_service.encrypt_text(document_text)
        encrypted_mapping = encryption_service.encrypt_dict(pii_mapping)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Encryption failed: {str(e)}"
        )
    
    # Step 5: Create session in database
    session_id = str(uuid.uuid4())
    
    anonymization_session = AnonymizationSession(
        id=session_id,
        user_id=current_user.id,
        original_filename=file.filename,
        document_text_encrypted=encrypted_original,
        anonymized_text=anonymized_text,
        pii_mapping_encrypted=encrypted_mapping,
        upload_timestamp=datetime.utcnow()
    )
    
    db.add(anonymization_session)
    
    # Step 6: Store individual PII mappings
    for original_value, placeholder in pii_mapping.items():
        # Determine PII type from placeholder
        pii_type = placeholder.split('[')[1].split('_')[0] if '[' in placeholder else 'UNKNOWN'
        
        # Find confidence score from entities
        confidence = 0.9
        detection_method = 'combined'
        for entity in entities:
            if entity['text'] == original_value:
                confidence = entity['confidence']
                detection_method = entity['detection_method']
                break
        
        encrypted_original_value = encryption_service.encrypt_text(original_value)
        
        pii_mapping_entry = PIIMapping(
            session_id=session_id,
            original_value_encrypted=encrypted_original_value,
            placeholder=placeholder,
            pii_type=pii_type,
            confidence_score=confidence,
            detection_method=detection_method
        )
        db.add(pii_mapping_entry)
    
    # Step 7: Log upload action
    audit_entry = AuditLog(
        user_id=current_user.id,
        session_id=session_id,
        action="DOCUMENT_UPLOADED",
        ip_address=None
    )
    db.add(audit_entry)
    
    try:
        db.commit()
        db.refresh(anonymization_session)
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database error: {str(e)}"
        )
    
    # Step 8: Get statistics
    stats = pii_detector.get_statistics(entities)
    
    return {
        "session_id": session_id,
        "filename": file.filename,
        "upload_timestamp": anonymization_session.upload_timestamp,
        "pii_detected_count": len(entities),
        "pii_types": list(stats['by_type'].keys()),
        "status": "completed"
    }


@router.get("/document/{session_id}", response_model=SessionDetailResponse)
async def get_document_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get detailed information about an anonymization session"""
    
    session = db.query(AnonymizationSession).filter(
        AnonymizationSession.id == session_id,
        AnonymizationSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Decrypt mapping
    try:
        pii_mapping = encryption_service.decrypt_dict(session.pii_mapping_encrypted)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to decrypt mapping"
        )
    
    # Get PII mappings with metadata
    pii_mappings = db.query(PIIMapping).filter(PIIMapping.session_id == session_id).all()
    
    mapping_list = []
    for i, mapping in enumerate(pii_mappings):
        mapping_list.append({
            "id": i + 1,
            "original_value": "[ENCRYPTED]",  # Don't expose original values without decryption
            "placeholder": mapping.placeholder,
            "pii_type": mapping.pii_type,
            "confidence_score": mapping.confidence_score,
            "detection_method": mapping.detection_method
        })
    
    # Update last accessed
    session.last_accessed = datetime.utcnow()
    db.commit()
    
    return {
        "session_id": session.id,
        "filename": session.original_filename,
        "upload_timestamp": session.upload_timestamp,
        "document_text": "[Original text is encrypted. Use Decrypt tab to view.]",
        "anonymized_text": session.anonymized_text,
        "pii_mappings": mapping_list,
        "export_count": session.export_count,
        "last_accessed": session.last_accessed
    }


@router.delete("/document/{session_id}")
async def delete_document_session(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete an anonymization session"""
    
    session = db.query(AnonymizationSession).filter(
        AnonymizationSession.id == session_id,
        AnonymizationSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found"
        )
    
    # Log deletion
    audit_entry = AuditLog(
        user_id=current_user.id,
        session_id=session_id,
        action="SESSION_DELETED",
        ip_address=None
    )
    db.add(audit_entry)
    
    # Delete related PII mappings
    db.query(PIIMapping).filter(PIIMapping.session_id == session_id).delete()
    
    # Delete session
    db.delete(session)
    db.commit()
    
    return {"message": "Session deleted successfully"}


@router.get("/documents", response_model=list)
async def list_user_documents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all anonymization sessions for the current user"""
    
    sessions = db.query(AnonymizationSession).filter(
        AnonymizationSession.user_id == current_user.id
    ).order_by(AnonymizationSession.upload_timestamp.desc()).all()
    
    result = []
    for session in sessions:
        # Count PII entries
        pii_count = db.query(PIIMapping).filter(PIIMapping.session_id == session.id).count()
        
        result.append({
            "session_id": session.id,
            "filename": session.original_filename,
            "upload_timestamp": session.upload_timestamp,
            "pii_count": pii_count,
            "export_count": session.export_count,
            "last_accessed": session.last_accessed
        })
    
    return result
