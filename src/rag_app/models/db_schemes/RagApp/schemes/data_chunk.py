from datetime import datetime

from pydantic import BaseModel
from sqlalchemy import Integer, String, DateTime,ForeignKey, UniqueConstraint, Index, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from .rag_base import SQLAlchemyBase

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .asset import Asset
    from .project import Project
    

class DataChunk(SQLAlchemyBase):
    __tablename__ = "chunks"

    chunk_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chunk_uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    chunk_text: Mapped[str] = mapped_column(String, nullable=False)
    chunk_metadata: Mapped[dict | None] = mapped_column(JSONB, nullable=True) # metadata
    chunk_order: Mapped[int] = mapped_column(Integer, nullable=False)
    
    
    chunk_project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.project_id"), nullable=False) # project_id
    chunk_asset_id: Mapped[int] = mapped_column(Integer, ForeignKey("assets.asset_id"), nullable=False) # asset_id
    
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at : Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)

    
    project: Mapped["Project"] = relationship("Project", back_populates="chunks")  # Establish relationship with Project
    asset: Mapped["Asset"] = relationship("Asset", back_populates="chunks")
    
    
    __table_args__ = (
                # Ensure chunks names are unique within each project cx
                UniqueConstraint("chunk_asset_id", "chunk_order", name="uq_chunk_asset_order"),
                # Add a unique constraint on chunks_name and chunk_project_id
                Index("ix_chunk_project_id", "chunk_project_id"),
                Index("ix_chunk_asset_id", "chunk_asset_id"),
            )
        
        
class RetrievedDocument(BaseModel):

    text : str
    score : float        