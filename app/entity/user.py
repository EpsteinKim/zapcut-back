from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime
import bcrypt


class User(SQLModel, table=True):
    __tablename__ = "user"

    id: Optional[int] = Field(default=None, primary_key=True)  # auto increment
    user_id: str = Field(unique=True, index=True, max_length=32)
    password: str = Field(max_length=64)
    name: str = Field(max_length=10)
    phone: str = Field(max_length=20)
    email: str = Field(max_length=32)
    status: str = Field(default="NORMAL", max_length=16)
    point_balance: int = Field(default=0)
    oauth_id: Optional[str] = Field(default=None, max_length=32)
    oauth_provider: Optional[str] = Field(default=None, max_length=16)
    created_at: Optional[datetime] = Field(default_factory=datetime.now, nullable=False)

    def set_password(self, password: str) -> None:
        """비밀번호를 암호화하여 저장"""
        salt = bcrypt.gensalt()
        self.password = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """비밀번호 검증"""
        return bcrypt.checkpw(password.encode("utf-8"), self.password.encode("utf-8"))


class UserCreate(SQLModel):
    """사용자 생성용 스키마"""

    user_id: str
    password: str
    name: str
    phone: str
    email: str


class UserResponse(SQLModel):
    """사용자 응답용 스키마 (비밀번호 제외)"""

    id: int
    user_id: str
    name: str
    phone: str
    email: str
    status: str
    point_balance: int
    oauth_id: Optional[str] = None
    oauth_provider: Optional[str] = None
    created_at: Optional[datetime] = None
