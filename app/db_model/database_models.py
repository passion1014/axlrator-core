from sqlalchemy import Boolean, Column, ForeignKey, Integer, String, CHAR, Text, Time, UUID
from sqlalchemy.orm import relationship

# database.py에서 생성한 Base import
from .database import Base

class ModelInfo(Base):
    '''
    모델 정보
    '''
    __tablename__ = "model_info"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String, index=True)
    desc = Column(Text, index=True)
    model_type = Column(CHAR(2), index=True)

    # VectorData와의 관계 설정
    vector_data = relationship("VectorData", back_populates="model_info")


class StoreInfo(Base):
    '''
    저장소 정보
    '''
    __tablename__ = "store_info"

    id = Column(Integer, primary_key=True, index=True)
    store_name = Column(String, index=True)
    store_type = Column(CHAR(2), index=True)

    # VectorData와의 관계 설정
    vector_data = relationship("VectorData", back_populates="store_info")


class OrgRSrc(Base):
    '''
    원본 리소스 정보
    '''
    __tablename__ = "org_resrc"

    id = Column(Integer, primary_key=True, index=True)
    resrc_name = Column(String, index=True)
    resrc_type = Column(CHAR(2), index=True)
    resrc_path = Column(Text, index=True)
    resrc_desc = Column(Text, index=True)

    # VectorData와의 관계 설정
    vector_data = relationship("VectorData", back_populates="org_resrc")


class VectorData(Base):
    '''
    벡터 데이터
    '''
    __tablename__ = "vector_data"

    id = Column(Integer, primary_key=True, index=True)
    store_info_id = Column(Integer, ForeignKey("store_info.id"))
    org_resrc_id = Column(Integer, ForeignKey("org_resrc.id"))
    model_info_id = Column(Integer, ForeignKey("model_info.id"))
    proc_time = Column(Time, index=True)

    # 관계 설정
    store_info = relationship("StoreInfo", back_populates="vector_data")
    org_resrc = relationship("OrgRSrc", back_populates="vector_data")
    model_info = relationship("ModelInfo", back_populates="vector_data")
    vector_data_chunk = relationship("VectorDataChunk", back_populates="vector_data")


class VectorDataChunk(Base):
    '''
    벡터 청크 데이터
    '''
    __tablename__ = "vector_data_chunk"

    id = Column(Integer, primary_key=True, index=True)
    vector_data_id = Column(Integer, ForeignKey("vector_data.id"))
    org_resrc_id = Column(Integer, ForeignKey("org_resrc.id"))
    chunk_id = Column(UUID, index=True)
    chunk_data = Column(Text, index=True)

    # VectorData와의 관계 설정
    vector_data = relationship("VectorData", back_populates="vector_data_chunk")
