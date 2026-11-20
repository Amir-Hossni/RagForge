from datetime import datetime

from sqlalchemy import Integer, String, DateTime,ForeignKey, UniqueConstraint, Index, func
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
import uuid

from .rag_base import SQLAlchemyBase

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .data_chunk import DataChunk
    from .project import Project
    
    
class Asset(SQLAlchemyBase):
    __tablename__ = "assets"

    asset_id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    asset_uuid: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    asset_type: Mapped[str] = mapped_column(String, nullable=False)
    asset_name: Mapped[str] = mapped_column(String, nullable=False)
    asset_size: Mapped[int] = mapped_column(Integer, nullable=False)
    asset_config: Mapped[dict] = mapped_column(JSONB, nullable=True) # metadata
    
    asset_project_id: Mapped[int] = mapped_column(Integer, ForeignKey("projects.project_id"), nullable=False) # project_id 
        
    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    project: Mapped["Project"] = relationship("Project", back_populates="assets")  # Establish relationship with Project
    chunks: Mapped[list["DataChunk"]] = relationship("DataChunk", back_populates="asset")
    
    __table_args__ = (
            # Ensure asset names are unique within each project cx
            UniqueConstraint("asset_name", "asset_project_id", name="uq_asset_name_project"),
            # Add a unique constraint on asset_name and asset_project_id
            Index('ix_asset_project_id', 'asset_project_id'),
            Index('ix_asset_type', 'asset_type'),
        )
    
    