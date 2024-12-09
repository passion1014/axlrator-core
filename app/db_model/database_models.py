from sqlalchemy import JSON, TIMESTAMP, BigInteger, Boolean, Column, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

# database.py에서 생성한 Base import
from .database import Base

class ModelInfo(Base):
    '''
    모델 정보
    '''
    __tablename__ = "model_info"

    id = Column(Integer, primary_key=True, index=True, comment="primary key")
    model_name = Column(String(512), comment="모델명")
    desc = Column(Text, comment="모델 설명")
    model_type = Column(String(2), index=True, comment="모델 유형") # 01:LLM Model, 02:Embedding Model
    model_version = Column(String(256), comment="모델 버전")

    modified_at = Column(TIMESTAMP, index=True, comment="최종수정시간")
    created_at = Column(TIMESTAMP, index=True, comment="생성시간")
    modified_by = Column(String(50), index=True, comment="최종수정자")
    created_by = Column(String(50), index=True, comment="생성자")



class OrgRSrc(Base):
    '''
    원본 리소스
    '''
    __tablename__ = "org_resrc"

    id = Column(Integer, primary_key=True, index=True, comment="primary key")
    resrc_name = Column(String, comment="리소스명")
    resrc_type = Column(String(4), index=True, comment="리소스 유형") # 코드
    resrc_path = Column(Text, comment="리소스 위치")
    resrc_desc = Column(Text, comment="리소스 상세")
    is_vector = Column(Boolean, default=False, comment="벡터화 여부")
    
    modified_at = Column(TIMESTAMP, index=True, comment="최종수정시간")
    created_at = Column(TIMESTAMP, index=True, comment="생성시간")
    modified_by = Column(String(50), index=True, comment="최종수정자")
    created_by = Column(String(50), index=True, comment="생성자")
    
    # 관계 설정
    org_resrc_code = relationship("OrgRSrcCode", back_populates="org_resrc")
    chunked_data = relationship("ChunkedData", back_populates="org_resrc")

    def __repr__(self):
        return f"OrgRSrc(id={self.id}, resrc_name='{self.resrc_name}', resrc_type='{self.resrc_type}', is_vector={self.is_vector})"

class OrgRSrcCode(Base):
    '''
    원본 리소스 코드 (OrgRSrc의 서브타입 : 프로그램 리소스일 경우)
    '''
    __tablename__ = "org_resrc_code"

    id = Column(Integer, primary_key=True, index=True, comment="primary key")  # 유일키
    org_resrc_id = Column(Integer, ForeignKey("org_resrc.id"), comment="OrgRSrc FK")  # ORG_RESRC 외래키

    project_info = Column(Text, comment="프로젝트 정보")  # 프로젝트 정보
    package_name = Column(Text, comment="패키지명")  # 패키지명
    class_type = Column(Text, comment="클래스타입")  # 클래스 타입
    class_name = Column(String, comment="클래스명")  # 클래스 명
    class_extends = Column(Text, comment="상속자")  # 상속자
    class_implements = Column(Text, comment="구현자")  # 구현자들
    class_imports = Column(Text, comment="임포트")  # 외포트들
    class_attributes = Column(Text, comment="어트리뷰트")  # 어트리뷰트들 (변수들)
    # class_methods_cnt = Column(Integer, comment="함수 갯수")  # 함수 갯수

    modified_at = Column(TIMESTAMP, index=True, comment="최종수정시간")
    created_at = Column(TIMESTAMP, index=True, comment="생성시간")
    modified_by = Column(String(50), index=True, comment="최종수정자")
    created_by = Column(String(50), index=True, comment="생성자")

    # 관계 설정
    org_resrc = relationship("OrgRSrc", back_populates="org_resrc_code")


class ChunkedData(Base):
    '''
    원본 리소스 인덱스 데이터
    '''
    __tablename__ = "chunked_data"

    id = Column(Integer, primary_key=True, index=True, comment="primary key")  # 유일키
    seq = Column(Integer, index=True, comment="순번")  # 순번
    org_resrc_id = Column(Integer, ForeignKey("org_resrc.id"), comment="OrgRSrc FK")  # ORG_RESRC 외래키
    data_name = Column(String, comment="데이터명")  # 데이터명
    data_type = Column(Text, comment="데이터 유형")  # 데이터 유형
    content = Column(Text, comment="콘텐츠")  # 콘텐츠
    context_chunk = Column(Text, comment="컨텍스트 청크")  # 컨텍스트 청크
    document_metadata = Column(JSON, comment="문서의 메타데이터")  # 문서의 메타데이터
    
    # 벡터 인덱스 정보\
    faiss_info_id = Column(Integer, ForeignKey("faiss_info.id"), comment="FaissInfo FK")  # FAISS_INFO 외래키
    vector_index = Column(BigInteger, index=True, comment="벡터 인덱스값")

    modified_at = Column(TIMESTAMP, index=True, comment="최종수정시간")
    created_at = Column(TIMESTAMP, index=True, comment="생성시간")
    modified_by = Column(String(50), index=True, comment="최종수정자")
    created_by = Column(String(50), index=True, comment="생성자")

    # 관계 설정
    org_resrc = relationship("OrgRSrc", back_populates="chunked_data")
    faiss_info = relationship("FaissInfo", back_populates="chunked_data")



class FaissInfo(Base):
    '''
    FAISS 인덱스 정보
    '''
    __tablename__ = "faiss_info"

    id = Column(Integer, primary_key=True, index=True, comment="primary key")  # 유일키
    index_name = Column(String, comment="인덱스명")
    index_desc = Column(Text, comment="인덱스 설명")
    index_file_path = Column(Text, comment="인덱스 파일 경로")
    
    modified_at = Column(TIMESTAMP, index=True, comment="최종수정시간")
    created_at = Column(TIMESTAMP, index=True, comment="생성시간")
    modified_by = Column(String(50), index=True, comment="최종수정자")
    created_by = Column(String(50), index=True, comment="생성자")

    # ChunkedData와의 관계 설정
    chunked_data = relationship("ChunkedData", back_populates="faiss_info")

class RSrcTable(Base):
    '''
    테이블 정보
    '''
    __tablename__ = "rsrc_table"

    id = Column(Integer, primary_key=True, index=True, comment="primary key")  # 유일키
    
    table_name = Column(String, comment="테이블명")  # 테이블명
    table_desc = Column(Text, comment="테이블 설명")  # 테이블 설명
    
    created_at = Column(TIMESTAMP, index=True, comment="생성시간")  # 생성시간
    modified_at = Column(TIMESTAMP, index=True, comment="최종수정시간")  # 최종수정시간
    created_by = Column(String(50), index=True, comment="생성자")  # 생성자
    modified_by = Column(String(50), index=True, comment="최종수정자")  # 최종수정자
    
    rsrc_table_column = relationship("RSrcTableColumn", back_populates="rsrc_table")


class RSrcTableColumn(Base):
    '''
    테이블 컬럼 정보
    '''
    __tablename__ = "rsrc_table_column"

    id = Column(Integer, primary_key=True, index=True, comment="primary key")  # 유일키
    
    column_name = Column(String, comment="컬럼명")  # 컬럼명
    column_korean_name = Column(String, comment="컬럼 한글명")  # 컬럼 한글명
    column_type = Column(String, comment="컬럼 타입")  # 컬럼 타입
    column_desc = Column(Text, comment="컬럼 설명")  # 컬럼 설명
    
    rsrc_table_id = Column(Integer, ForeignKey('rsrc_table.id'), comment="rsrc_table FK")  # 테이블 ID
    
    created_at = Column(TIMESTAMP, index=True, comment="생성시간")  # 생성시간
    modified_at = Column(TIMESTAMP, index=True, comment="최종수정시간")  # 최종수정시간
    created_by = Column(String(50), index=True, comment="생성자")  # 생성자
    modified_by = Column(String(50), index=True, comment="최종수정자")  # 최종수정자

    # RSrcTable와의 관계 설정
    rsrc_table = relationship("RSrcTable", back_populates="rsrc_table_column")
