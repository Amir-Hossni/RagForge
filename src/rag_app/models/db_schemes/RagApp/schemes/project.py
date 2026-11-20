from sqlalchemy import Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column ,relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime

from .rag_base import SQLAlchemyBase

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .data_chunk import DataChunk
    from .asset import Asset
    
    
class Project(SQLAlchemyBase):
    __tablename__ = "projects"

    project_id : Mapped[int]  = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_uuid : Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), unique=True, nullable=False, default=uuid.uuid4)

    created_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at : Mapped[datetime] = mapped_column(DateTime(timezone=True), onupdate=func.now(), nullable=True)
    
    assets: Mapped[list["Asset"]] = relationship("Asset", back_populates="project", cascade="all, delete-orphan")
    chunks: Mapped[list["DataChunk"]] = relationship("DataChunk", back_populates="project")