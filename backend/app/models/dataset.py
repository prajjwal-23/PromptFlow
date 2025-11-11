"""
Dataset and document models.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Integer, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Dataset(Base):
    """Dataset model for knowledge bases."""
    
    __tablename__ = "datasets"
    
    id = Column(String, primary_key=True, index=True)
    workspace_id = Column(String, ForeignKey("workspaces.id"), nullable=False)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    vector_store = Column(String, default="qdrant", nullable=False)  # Vector store type
    embedding_model = Column(String, nullable=True)  # Embedding model used
    chunk_size = Column(Integer, default=1000, nullable=False)
    chunk_overlap = Column(Integer, default=200, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    workspace = relationship("Workspace", back_populates="datasets")
    creator = relationship("User", back_populates="datasets")
    documents = relationship("Document", back_populates="dataset")
    
    def __repr__(self):
        return f"<Dataset(id={self.id}, name={self.name}, workspace_id={self.workspace_id})>"


class Document(Base):
    """Document model for uploaded files."""
    
    __tablename__ = "documents"
    
    id = Column(String, primary_key=True, index=True)
    dataset_id = Column(String, ForeignKey("datasets.id"), nullable=False)
    filename = Column(String, nullable=False)
    original_name = Column(String, nullable=False)
    file_type = Column(String, nullable=False)  # pdf, txt, md, etc.
    file_size = Column(Integer, nullable=False)
    uri = Column(String, nullable=False)  # Storage URI (MinIO path)
    status = Column(String, default="uploaded", nullable=False)  # uploaded, processing, indexed, error
    error_message = Column(Text, nullable=True)
    document_metadata = Column(Text, nullable=True)  # JSON metadata (renamed from metadata)
    indexed_at = Column(DateTime(timezone=True), nullable=True)  # When document was indexed
    created_by = Column(String, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    dataset = relationship("Dataset", back_populates="documents")
    creator = relationship("User", back_populates="documents")
    
    def __repr__(self):
        return f"<Document(id={self.id}, filename={self.filename}, dataset_id={self.dataset_id})>"