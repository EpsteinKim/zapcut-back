from sqlmodel import SQLModel, Field
from typing import Optional
import bcrypt


class User(SQLModel, table=True):
    """사용자 테이블"""

    id: Optional[int] = Field(default=None, primary_key=True)  # auto increment
    username: str = Field(unique=True, index=True, max_length=50)
    password_hash: str = Field(max_length=255)
    created_at: Optional[str] = Field(default=None)

    def set_password(self, password: str) -> None:
        """비밀번호를 암호화하여 저장"""
        salt = bcrypt.gensalt()
        self.password_hash = bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")

    def check_password(self, password: str) -> bool:
        """비밀번호 검증"""
        return bcrypt.checkpw(password.encode("utf-8"), self.password_hash.encode("utf-8"))


class UserCreate(SQLModel):
    """사용자 생성용 스키마"""

    username: str
    password: str


class UserResponse(SQLModel):
    """사용자 응답용 스키마 (비밀번호 제외)"""

    id: int
    username: str
    created_at: Optional[str] = None
