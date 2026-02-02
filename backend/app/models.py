from sqlalchemy import Column, Integer, String, Text, DateTime, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(255), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = relationship("AnonymizationSession", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class AnonymizationSession(Base):
    """Anonymization session model"""
    __tablename__ = "anonymization_sessions"
    
    id = Column(String(36), primary_key=True)  # UUID
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    original_filename = Column(String(255))
    upload_timestamp = Column(DateTime, default=datetime.utcnow)
    document_text_encrypted = Column(Text, nullable=False)
    anonymized_text = Column(Text, nullable=False)
    pii_mapping_encrypted = Column(Text, nullable=False)
    export_count = Column(Integer, default=0)
    last_accessed = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")
    pii_mappings = relationship("PIIMapping", back_populates="session", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="session", cascade="all, delete-orphan")


class PIIMapping(Base):
    """PII mapping model"""
    __tablename__ = "pii_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(36), ForeignKey("anonymization_sessions.id"), nullable=False)
    original_value_encrypted = Column(Text, nullable=False)
    placeholder = Column(String(50), nullable=False)
    pii_type = Column(String(50))  # PERSON, EMAIL, PHONE, SSN, etc.
    confidence_score = Column(Float)
    detection_method = Column(String(50))  # spacy, regex
    
    # Relationships
    session = relationship("AnonymizationSession", back_populates="pii_mappings")


class AuditLog(Base):
    """Audit log model"""
    __tablename__ = "audit_log"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id = Column(String(36), ForeignKey("anonymization_sessions.id"))
    action = Column(String(50), nullable=False)  # upload, decrypt, export, delete
    timestamp = Column(DateTime, default=datetime.utcnow)
    ip_address = Column(String(45))
    details = Column(Text)  # JSON string with additional details
    
    # Relationships
    user = relationship("User", back_populates="audit_logs")
    session = relationship("AnonymizationSession", back_populates="audit_logs")
