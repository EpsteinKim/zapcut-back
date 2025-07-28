from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class PointTransaction(SQLModel, table=True):
    __tablename__ = "point_transaction"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(index=True)
    type: str = Field(max_length=16)
    amount: int
    description: str = Field(max_length=32)
    payment_method: str = Field(max_length=16)
    created_at: Optional[datetime] = Field(default_factory=datetime.now, nullable=False)
    updated_at: Optional[datetime] = Field(default_factory=datetime.now, nullable=False)
