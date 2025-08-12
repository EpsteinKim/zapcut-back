from typing import Optional, Dict, Any
from datetime import datetime
from sqlmodel import Field, SQLModel, JSON


class Shorts(SQLModel, table=True):
    __tablename__ = "shorts"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    status: str = Field(default="ACTIVE")  # ACTIVE, DELETED
    title: str = Field(max_length=50)
    shorts_json: Dict[str, Any] = Field(sa_type=JSON)
    created_at: Optional[datetime] = Field(default_factory=datetime.now, nullable=False)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now, nullable=False)
