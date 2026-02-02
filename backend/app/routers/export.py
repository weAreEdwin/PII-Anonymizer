"""
Export Router - Endpoints for exporting anonymized documents
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Literal

from ..database import get_db
from ..models import User, AnonymizationSession, PIIMapping
from ..utils.security import get_current_user
from ..services.export_service import ExportService
from ..schemas import ExportResponse

router = APIRouter(prefix="/api/export", tags=["export"])
export_service = ExportService()


@router.get("/{session_id}/{format}")
async def export_document(
    session_id: str,
    format: Literal["pdf", "docx", "txt", "json"],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export anonymized document in specified format
    
    Args:
        session_id: Session identifier
        format: Export format (pdf, docx, txt, json)
        current_user: Authenticated user
        db: Database session
        
    Returns:
        StreamingResponse: File download
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
    
    # Prepare metadata
    metadata = {
        "pii_count": len(session.pii_mappings),
        "upload_timestamp": session.upload_timestamp.isoformat(),
        "user": current_user.username
    }
    
    # Generate export based on format
    try:
        if format == "pdf":
            buffer = await export_service.export_as_pdf(
                anonymized_text=session.anonymized_text,
                filename=session.original_filename,
                session_id=session_id,
                metadata=metadata
            )
            media_type = "application/pdf"
            file_extension = "pdf"
            
        elif format == "docx":
            buffer = await export_service.export_as_docx(
                anonymized_text=session.anonymized_text,
                filename=session.original_filename,
                session_id=session_id,
                metadata=metadata
            )
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            file_extension = "docx"
            
        elif format == "txt":
            buffer = await export_service.export_as_txt(
                anonymized_text=session.anonymized_text,
                filename=session.original_filename,
                session_id=session_id,
                metadata=metadata
            )
            media_type = "text/plain"
            file_extension = "txt"
            
        elif format == "json":
            # For JSON, export the PII mappings
            mappings = [
                {
                    "original": mapping.original_value_encrypted,  # Note: still encrypted
                    "placeholder": mapping.placeholder,
                    "pii_type": mapping.pii_type,
                    "confidence_score": mapping.confidence_score,
                    "detection_method": mapping.detection_method
                }
                for mapping in session.pii_mappings
            ]
            
            buffer = await export_service.export_mapping_as_json(
                pii_mappings=mappings,
                session_id=session_id,
                filename=session.original_filename,
                metadata=metadata
            )
            media_type = "application/json"
            file_extension = "json"
        
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format: {format}"
            )
        
        # Update export count
        session.export_count += 1
        db.commit()
        
        # Generate filename
        base_name = session.original_filename.rsplit('.', 1)[0] if '.' in session.original_filename else session.original_filename
        download_filename = f"{base_name}_anonymized.{file_extension}"
        
        # Return file as streaming response
        return StreamingResponse(
            buffer,
            media_type=media_type,
            headers={
                "Content-Disposition": f"attachment; filename={download_filename}"
            }
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.get("/{session_id}/mapping/json", response_model=ExportResponse)
async def export_pii_mapping(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Export PII mapping as JSON (separate endpoint for clarity)
    
    Args:
        session_id: Session identifier
        current_user: Authenticated user
        db: Database session
        
    Returns:
        ExportResponse: Export confirmation with download URL
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
    
    return ExportResponse(
        session_id=session_id,
        filename=session.original_filename,
        format="json",
        download_url=f"/api/export/{session_id}/json",
        message="PII mapping ready for download"
    )
