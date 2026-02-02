"""
Chat Router - Endpoints for Q&A on anonymized documents
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import User, AnonymizationSession
from ..utils.security import get_current_user
from ..services.chat_service import ChatService
from ..schemas import ChatRequest, ChatResponse, ChatHistoryResponse

router = APIRouter(prefix="/api/chat", tags=["chat"])
chat_service = ChatService()


@router.post("/{session_id}", response_model=ChatResponse)
async def send_message(
    session_id: str,
    chat_request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Send a message/question about the anonymized document
    
    Args:
        session_id: Session identifier
        chat_request: Contains the user's message
        current_user: Authenticated user
        db: Database session
        
    Returns:
        ChatResponse: Bot's response with context
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
    
    # Process the query
    try:
        response_text, contexts = await chat_service.process_query(
            session_id=session_id,
            query=chat_request.message,
            document=session.anonymized_text
        )
        
        return ChatResponse(
            session_id=session_id,
            user_message=chat_request.message,
            bot_response=response_text,
            contexts=[ctx['text'] for ctx in contexts],
            context_count=len(contexts)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Chat processing failed: {str(e)}"
        )


@router.get("/{session_id}/history", response_model=ChatHistoryResponse)
async def get_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get chat history for a session
    
    Args:
        session_id: Session identifier
        current_user: Authenticated user
        db: Database session
        
    Returns:
        ChatHistoryResponse: List of chat messages
    """
    # Verify session exists and user has access
    session = db.query(AnonymizationSession).filter(
        AnonymizationSession.id == session_id,
        AnonymizationSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied"
        )
    
    # Get chat history from service
    history = chat_service.get_chat_history(session_id)
    
    return ChatHistoryResponse(
        session_id=session_id,
        message_count=len(history),
        messages=history
    )


@router.delete("/{session_id}/clear")
async def clear_chat_history(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Clear chat history for a session
    
    Args:
        session_id: Session identifier
        current_user: Authenticated user
        db: Database session
        
    Returns:
        dict: Confirmation message
    """
    # Verify session exists and user has access
    session = db.query(AnonymizationSession).filter(
        AnonymizationSession.id == session_id,
        AnonymizationSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found or access denied"
        )
    
    # Clear history
    chat_service.clear_chat_history(session_id)
    
    return {
        "session_id": session_id,
        "message": "Chat history cleared successfully"
    }


@router.get("/{session_id}/suggestions")
async def get_question_suggestions(
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get suggested questions based on document content
    
    Args:
        session_id: Session identifier
        current_user: Authenticated user
        db: Database session
        
    Returns:
        dict: List of suggested questions
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
    
    # Get PII types from mappings
    pii_types = list(set([mapping.pii_type for mapping in session.pii_mappings]))
    
    # Generate suggestions
    suggestions = chat_service.suggest_questions(
        document=session.anonymized_text,
        pii_types=pii_types
    )
    
    return {
        "session_id": session_id,
        "suggestions": suggestions,
        "pii_types_detected": pii_types
    }
