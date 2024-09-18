from sqlalchemy import JSON, TIMESTAMP, BigInteger, Boolean, Column, ForeignKey, Integer, String, CHAR, Text, Time, UUID
from sqlalchemy.orm import relationship

# database.py에서 생성한 Base import
from .database import Base

class ModelInfo(Base):
    '''
    모델 정보
    '''
    __tablename__ = "model_info"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(512))
    desc = Column(Text)
    model_type = Column(String(2), index=True) # 01:LLM Model, 02:Embedding Model
    model_version = Column(String(256))

    # # VectorData와의 관계 설정
    # vector_data = relationship("VectorData", back_populates="model_info")


class FaissInfo(Base):
    '''
    FAISS INFO
    '''
    __tablename__ = "faiss_info"

    id = Column(Integer, primary_key=True, index=True)
    
    index_name = Column(String(512))
    index_desc = Column(Text)
    index_file_path = Column(Text)

    # # VectorData와의 관계 설정
    # vector_data = relationship("VectorData", back_populates="model_info")


class OrgRSrc(Base):
    '''
    원본 리소스
    '''
    __tablename__ = "org_resrc"

    id = Column(Integer, primary_key=True, index=True)  # 유일키
    resrc_name = Column(String)  # 리소스명
    resrc_type = Column(String(4), index=True)  # 리소스 유형 (코드)
    resrc_path = Column(Text)  # 리소스 위치
    resrc_desc = Column(Text)  # 리소스 상세
    last_modified_time = Column(TIMESTAMP)  # 최종 수정일
    
    is_vector = Column(Boolean, default=False) # 벡터화 여부
    
    faiss_info_id = Column(Integer, ForeignKey("faiss_info.id"))  # FaissInfo FK

    # OrgRSrcCode와의 관계 설정
    org_resrc_code = relationship("OrgRSrcCode", back_populates="org_resrc")
    
    # OrgRSrcData와의 관계 설정
    org_resrc_data = relationship("OrgRSrcData", back_populates="org_resrc")


class OrgRSrcCode(Base):
    '''
    원본 리소스 코드 (OrgRSrc의 서브타입 : 프로그램 리소스일 경우)
    '''
    __tablename__ = "org_resrc_code"

    id = Column(Integer, primary_key=True, index=True)  # 유일키
    org_resrc_id = Column(Integer, ForeignKey("org_resrc.id"))  # ORG_RESRC 외래키

    project_info = Column(Text)  # 프로젝트 정보
    package_name = Column(Text)  # 패키지명
    class_type = Column(Text)  # 클래스 타입
    class_name = Column(String)  # 클래스 명
    class_extends = Column(Text)  # 상속자
    class_implements = Column(Text)  # 구현자들
    class_imports = Column(Text)  # 외포트들
    class_attributes = Column(Text)  # 어트리뷰트들 (변수들)
    class_methods_cnt = Column(Integer)  # 함수 갯수
    last_modified_time = Column(TIMESTAMP, index=True)  # 최종 수정일

    # 관계 설정
    org_resrc = relationship("OrgRSrc", back_populates="org_resrc_code")


class OrgRSrcData(Base):
    '''
    원본 리소스 정보
    '''
    __tablename__ = "org_resrc_data"

    id = Column(Integer, primary_key=True, index=True)  # 유일키
    seq = Column(Integer, index=True)  # 순번
    org_resrc_id = Column(Integer, ForeignKey("org_resrc.id"))  # ORG_RESRC 외래키
    data_name = Column(String)  # 데이터명
    data_type = Column(Text)  # 데이터 유형
    content = Column(Text)  # 콘텐츠
    vector_index = Column(BigInteger, index=True)  # 벡터 인덱스번호
    document_metadata = Column(JSON)  # 문서의 메타데이터
    create_at = Column(TIMESTAMP, index=True)  # 생성시간

    # OrgRSrcDataCode와의 관계 설정
    org_resrc_data_code = relationship("OrgRSrcDataCode", back_populates="org_resrc_data")
    
    # 관계 설정
    org_resrc = relationship("OrgRSrc", back_populates="org_resrc_data")


class OrgRSrcDataCode(Base):
    '''
    원본 리소스 데이터 코드 (OrgRSrcData의 서브타입 : 프로그램 리소스일 경우)
    '''
    __tablename__ = "org_resrc_data_code"

    id = Column(Integer, primary_key=True, index=True)  # 유일키
    org_resrc_data_id = Column(Integer, ForeignKey("org_resrc_data.id"))  # ORG_RESRC_DATA 외래키
    return_type = Column(Text)  # 함수 리턴 타입
    parameter = Column(Text)  # 파라미터
    create_at = Column(TIMESTAMP, index=True)  # 생성시간

    # 관계 설정
    org_resrc_data = relationship("OrgRSrcData", back_populates="org_resrc_data_code")


class DocstoreIndex(Base):
    '''
    document와 vector index 매핑 정보
    '''
    __tablename__ = "docstore_index"
    
    id = Column(Integer, primary_key=True, index=True)  # 유일키
    index = Column(Integer, index=True)
    document_id = Column(Integer, ForeignKey("org_resrc_data.id"), nullable=False)