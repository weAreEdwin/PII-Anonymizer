from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
from datetime import datetime


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """Base user schema"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr


class UserCreate(UserBase):
    """User creation schema"""
    password: str = Field(..., min_length=8, max_length=100)


class UserLogin(BaseModel):
    """User login schema"""
    username: str
    password: str


class UserResponse(UserBase):
    """User response schema"""
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    """JWT token response"""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data"""
    username: Optional[str] = None


# ============================================================================
# Document Upload Schemas
# ============================================================================

class DocumentUploadResponse(BaseModel):
    """Document upload response"""
    session_id: str
    filename: str
    message: str
    processing_time: float


# ============================================================================
# PII Detection & Anonymization Schemas
# ============================================================================

class PIIMappingItem(BaseModel):
    """Single PII mapping item"""
    original: str
    placeholder: str
    pii_type: str
    confidence_score: Optional[float] = None
    detection_method: str


class PIIMappingResponse(BaseModel):
    """PII mapping response"""
    session_id: str
    mappings: List[PIIMappingItem]
    total_pii_detected: int


class AnonymizationPreview(BaseModel):
    """Anonymization preview with split view"""
    session_id: str
    original_filename: str
    original_text: str
    anonymized_text: str
    pii_count: int
    upload_timestamp: datetime


# ============================================================================
# Decryption Schemas
# ============================================================================

class DecryptRequest(BaseModel):
    """Decryption request"""
    password: str


class DecryptResponse(BaseModel):
    """Decryption response"""
    session_id: str
    original_text: str
    decrypted_at: datetime
    message: str


# ============================================================================
# Export Schemas
# ============================================================================

class ExportResponse(BaseModel):
    """Export response"""
    session_id: str
    filename: str
    format: str
    download_url: str
    message: str


# ============================================================================
# Chat Schemas
# ============================================================================

class ChatRequest(BaseModel):
    """Chat request"""
    message: str


class ChatResponse(BaseModel):
    """Chat response"""
    session_id: str
    user_message: str
    bot_response: str
    contexts: List[str] = []
    context_count: int = 0


class ChatHistoryResponse(BaseModel):
    """Chat history response"""
    session_id: str
    message_count: int
    messages: List[Dict[str, str]]


# ============================================================================
# Session Schemas
# ============================================================================

class SessionListItem(BaseModel):
    """Session list item"""
    session_id: str
    original_filename: str
    upload_timestamp: datetime
    last_accessed: datetime
    export_count: int
    pii_count: int


class SessionListResponse(BaseModel):
    """Session list response"""
    sessions: List[SessionListItem]
    total_count: int


class SessionResponse(BaseModel):
    """Session response after upload"""
    session_id: str
    filename: str
    upload_timestamp: datetime
    pii_detected_count: int
    pii_types: List[str]
    status: str


class SessionDetailResponse(BaseModel):
    """Detailed session response"""
    session_id: str
    filename: str
    upload_timestamp: datetime
    document_text: str
    anonymized_text: str
    pii_mappings: List[Dict]
    export_count: int
    last_accessed: datetime


class SessionDeleteResponse(BaseModel):
    """Session delete response"""
    session_id: str
    message: str


# ============================================================================
# Audit Log Schemas
# ============================================================================

class AuditLogEntry(BaseModel):
    """Audit log entry"""
    id: int
    action: str
    timestamp: datetime
    session_id: Optional[str] = None
    ip_address: Optional[str] = None
    details: Optional[str] = None
    
    class Config:
        from_attributes = True


# ============================================================================
# Error Schemas
# ============================================================================

class ErrorResponse(BaseModel):
    """Error response"""
    detail: str
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
