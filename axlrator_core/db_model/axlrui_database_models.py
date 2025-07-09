from sqlalchemy import JSON, TIMESTAMP, BigInteger, Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from sqlalchemy import Column, String, Text, JSON, BigInteger
from .axlrui_database import Base  # axlrui 전용 Base를 임포트해야 함

class File(Base):
    __tablename__ = "file"

    id = Column(Text, primary_key=True, index=True, comment="파일 ID")
    user_id = Column(Text, nullable=False, comment="사용자 ID")
    filename = Column(Text, nullable=False, comment="파일 이름")
    meta = Column(JSON, nullable=True, comment="메타 정보")
    created_at = Column(BigInteger, nullable=False, comment="생성일시 (UNIX Timestamp)")
    hash = Column(Text, nullable=True, comment="파일 해시")
    data = Column(JSON, nullable=True, comment="파일 데이터")
    updated_at = Column(BigInteger, nullable=True, comment="업데이트 일시 (UNIX Timestamp)")
    path = Column(Text, nullable=True, comment="파일 경로")
    access_control = Column(JSON, nullable=True, comment="접근 제어 정보")