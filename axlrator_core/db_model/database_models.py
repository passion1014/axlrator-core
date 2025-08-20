from sqlalchemy import JSON, TIMESTAMP, BigInteger, Boolean, Column, ForeignKey, Integer, String, Text, Numeric, CheckConstraint, UniqueConstraint, Index, text, desc, Identity
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB

# database.py에서 생성한 Base import
from .database import Base
# from .database_alembic import Base # alembic 실행시 이것을 사용

class ModelInfo(Base):
    '''
    모델 정보
    '''
    __tablename__ = "model_info"

    id = Column(BigInteger, Identity(), primary_key=True, comment="primary key")
    model_name = Column(String(512), comment="모델명")
    desc = Column(Text, comment="모델 설명")
    model_type = Column(String(2), index=True, comment="모델 유형") # 01:LLM Model, 02:Embedding Model
    model_version = Column(String(256), comment="모델 버전")

    modified_at = Column(TIMESTAMP, index=True, comment="최종수정시간")
    created_at = Column(TIMESTAMP, index=True, comment="생성시간")
    modified_by = Column(String(50), index=True, comment="최종수정자")
    created_by = Column(String(50), index=True, comment="생성자")

class UserInfo(Base):
    '''
    사용자 정보
    '''
    __tablename__ = "user_info"
    
    def __init__(self, user_id: str, password: str, email: str = None, user_name: str = None, is_active: bool = True):
        self.user_id = user_id
        self.password = password
        self.email = email
        self.user_name = user_name
        self.is_active = is_active

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"), comment="primary key")
    user_id = Column(String(256), unique=True, index=True, nullable=False, comment="아이디")
    password = Column(String(512), nullable=False, comment="비밀번호")
    email = Column(String(256), unique=True, index=True, nullable=False, comment="이메일 주소")
    user_name = Column(String(256), comment="전체 이름")
    is_active = Column(Boolean, default=True, comment="활성 상태")

    modified_at = Column(TIMESTAMP, index=True, comment="최종수정시간")
    created_at = Column(TIMESTAMP, index=True, comment="생성시간")
    modified_by = Column(String(50), index=True, comment="최종수정자")
    created_by = Column(String(50), index=True, comment="생성자")
    
    # 관계 설정
    chat_histories = relationship("ChatHistory", back_populates="user_info")


    def __repr__(self):
        return f"UserInfo(id={self.id}, username='{self.user_id}', email='{self.email}', is_active={self.is_active})"

class ChatHistory(Base):
    '''
    채팅 기록
    '''
    __tablename__ = "chat_history"

    id = Column(BigInteger, Identity(), primary_key=True, comment="primary key")
    thread_id = Column(String(100), comment="thread id")
    data = Column(Text, comment="큰 사이즈의 텍스트 컬럼")
    title = Column(String(200), comment="200자 사이즈 텍스트")
    type_code = Column(String(100), comment="타입코드") # code_assist:코드생성, text2sql:SQL생성
    user_info_id = Column(PGUUID(as_uuid=True), ForeignKey("user_info.id"), comment="UserInfo FK")

    modified_at = Column(TIMESTAMP, index=True, comment="최종수정시간")
    created_at = Column(TIMESTAMP, index=True, comment="생성시간")
    modified_by = Column(String(50), index=True, comment="최종수정자")
    created_by = Column(String(50), index=True, comment="생성자")

    # 관계 설정
    user_info = relationship("UserInfo", back_populates="chat_histories")

    def __repr__(self):
        return f"ChatHistory(id={self.id}, title='{self.title}', user_id={self.user_info_id})"

class OrgRSrc(Base):
    '''
    원본 리소스
    '''
    __tablename__ = "org_resrc"

    id = Column(BigInteger, Identity(), primary_key=True, comment="primary key")
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

    id = Column(BigInteger, Identity(), primary_key=True, comment="primary key")  # 유일키
    org_resrc_id = Column(BigInteger, ForeignKey("org_resrc.id"), comment="OrgRSrc FK")  # ORG_RESRC 외래키

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

    id = Column(BigInteger, Identity(), primary_key=True, comment="primary key")  # 유일키
    seq = Column(Integer, index=True, comment="순번")  # 순번
    org_resrc_id = Column(BigInteger, ForeignKey("org_resrc.id"), comment="OrgRSrc FK")  # ORG_RESRC 외래키
    data_name = Column(String, comment="데이터명")  # 데이터명
    data_type = Column(Text, comment="데이터 유형")  # 데이터 유형
    content = Column(Text, comment="콘텐츠")  # 콘텐츠
    context_chunk = Column(Text, comment="컨텍스트 청크")  # 컨텍스트 청크
    document_metadata = Column(JSON, comment="문서의 메타데이터")  # 문서의 메타데이터
    
    # 벡터 인덱스 정보\
    # faiss_info_id = Column(Integer, ForeignKey("faiss_info.id"), comment="FaissInfo FK")  # FAISS_INFO 외래키
    vector_index = Column(BigInteger, index=True, comment="벡터 인덱스값")

    modified_at = Column(TIMESTAMP, index=True, comment="최종수정시간")
    created_at = Column(TIMESTAMP, index=True, comment="생성시간")
    modified_by = Column(String(50), index=True, comment="최종수정자")
    created_by = Column(String(50), index=True, comment="생성자")

    # 관계 설정
    org_resrc = relationship("OrgRSrc", back_populates="chunked_data")
    # faiss_info = relationship("FaissInfo", back_populates="chunked_data")

    def to_dict(self):
        return {
            'id': self.id,
            'seq': self.seq,
            'org_resrc_id': self.org_resrc_id,
            'data_name': self.data_name,
            'data_type': self.data_type,
            'content': self.content,
            'context_chunk': self.context_chunk,
            'document_metadata': self.document_metadata,
            # 'faiss_info_id': self.faiss_info_id,
            'vector_index': self.vector_index,
            'modified_at': str(self.modified_at),
            'created_at': str(self.created_at),
            'modified_by': self.modified_by,
            'created_by': self.created_by
        }


class FaissInfo(Base):
    '''
    FAISS 인덱스 정보
    '''
    __tablename__ = "faiss_info"

    id = Column(BigInteger, Identity(), primary_key=True, comment="primary key")  # 유일키
    index_name = Column(String, comment="인덱스명")
    index_desc = Column(Text, comment="인덱스 설명")
    index_file_path = Column(Text, comment="인덱스 파일 경로")
    
    modified_at = Column(TIMESTAMP, index=True, comment="최종수정시간")
    created_at = Column(TIMESTAMP, index=True, comment="생성시간")
    modified_by = Column(String(50), index=True, comment="최종수정자")
    created_by = Column(String(50), index=True, comment="생성자")

    # ChunkedData와의 관계 설정
    # chunked_data = relationship("ChunkedData", back_populates="faiss_info")
    
    def to_dict(self):
        return {
            'id': self.id,
            'index_name': self.index_name,
            'index_desc': self.index_desc,
            'index_file_path': self.index_file_path,
            'modified_at': str(self.modified_at),
            'created_at': str(self.created_at),
            'modified_by': self.modified_by,
            'created_by': self.created_by
        }

class RSrcTable(Base):
    '''
    테이블 정보
    '''
    __tablename__ = "rsrc_table"

    id = Column(BigInteger, Identity(), primary_key=True, comment="primary key")  # 유일키
    
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

    id = Column(BigInteger, Identity(), primary_key=True, comment="primary key")  # 유일키
    
    column_name = Column(String, comment="컬럼명")  # 컬럼명
    column_korean_name = Column(String, comment="컬럼 한글명")  # 컬럼 한글명
    column_type = Column(String, comment="컬럼 타입")  # 컬럼 타입
    column_desc = Column(Text, comment="컬럼 설명")  # 컬럼 설명
    
    rsrc_table_id = Column(BigInteger, ForeignKey('rsrc_table.id'), comment="rsrc_table FK")  # 테이블 ID
    
    created_at = Column(TIMESTAMP, index=True, comment="생성시간")  # 생성시간
    modified_at = Column(TIMESTAMP, index=True, comment="최종수정시간")  # 최종수정시간
    created_by = Column(String(50), index=True, comment="생성자")  # 생성자
    modified_by = Column(String(50), index=True, comment="최종수정자")  # 최종수정자

    # RSrcTable와의 관계 설정
    rsrc_table = relationship("RSrcTable", back_populates="rsrc_table_column")


class CodeScanRun(Base):
    """
    실행 이력 (scan_runs)
    """
    __tablename__ = "code_scan_runs"

    id = Column(PGUUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"), comment="primary key")
    run_id = Column(String, unique=True, nullable=False, comment="Airflow/시스템 run 식별자")
    repo_url = Column(Text, nullable=False, comment="저장소 URL")
    ref = Column(Text, nullable=False, comment="브랜치/태그")
    range_spec = Column(Text, comment="base..head, commit range")
    started_at = Column(TIMESTAMP(timezone=True), server_default=text("now()"))
    finished_at = Column(TIMESTAMP(timezone=True))
    status = Column(String, nullable=False)
    policy_yaml = Column(Text, comment="실행 시점 정책 스냅샷")
    artifact_dir = Column(Text, comment="아티팩트 경로 또는 버킷 키")
    metrics = Column(JSONB, comment="duration, tokens, 비용 등")
    
    created_at = Column(TIMESTAMP, index=True, comment="생성시간")  # 생성시간
    modified_at = Column(TIMESTAMP, index=True, comment="최종수정시간")  # 최종수정시간
    created_by = Column(String(50), index=True, comment="생성자")  # 생성자
    modified_by = Column(String(50), index=True, comment="최종수정자")  # 최종수정자


    # 관계
    findings = relationship("Finding", back_populates="scan_run", cascade="all, delete-orphan")
    review_comments = relationship("ReviewComment", back_populates="scan_run", cascade="all, delete-orphan")
    convention_violations = relationship("ConventionViolation", back_populates="scan_run", cascade="all, delete-orphan")
    lint_violations = relationship("LintViolation", back_populates="scan_run", cascade="all, delete-orphan")
    artifacts = relationship("Artifact", back_populates="scan_run", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("status IN ('SUCCESS','FAILED','PARTIAL')", name="ck_scan_runs_status"),
        UniqueConstraint('repo_url', 'run_id', name='uq_scan_runs_repo_run'),
    )

    def __repr__(self):
        return f"CodeScanRun(id={self.id}, run_id={self.run_id}, status={self.status})"


class Finding(Base):
    """
    취약점/보안/시크릿 등 통합 결과 (findings)
    """
    __tablename__ = "findings"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    scan_run_id = Column(PGUUID(as_uuid=True), ForeignKey("code_scan_runs.id", ondelete="CASCADE"), nullable=False)
    tool = Column(Text, nullable=False)  # 'semgrep' | 'gitleaks' | 'llm' | ...
    rule_id = Column(Text)
    severity = Column(String, nullable=False)
    cwe = Column(Text)
    owasp = Column(Text)
    title = Column(Text, nullable=False)
    file_path = Column(Text)
    start_line = Column(Integer)
    end_line = Column(Integer)
    fingerprint = Column(Text, comment="중복 억제용 해시")
    rationale = Column(Text)
    patch = Column(Text)
    meta = Column(JSONB)

    created_at = Column(TIMESTAMP, index=True, comment="생성시간")  # 생성시간
    modified_at = Column(TIMESTAMP, index=True, comment="최종수정시간")  # 최종수정시간
    created_by = Column(String(50), index=True, comment="생성자")  # 생성자
    modified_by = Column(String(50), index=True, comment="최종수정자")  # 최종수정자


    scan_run = relationship("CodeScanRun", back_populates="findings")

    __table_args__ = (
        CheckConstraint("severity IN ('HIGH','MEDIUM','LOW','INFO')", name="ck_findings_severity"),
        UniqueConstraint('scan_run_id', 'fingerprint', name='uq_findings_fingerprint'),
    )

    def __repr__(self):
        return f"Finding(id={self.id}, severity={self.severity}, title={self.title})"


class ReviewComment(Base):
    """
    LLM/리뷰 코멘트 (review_comments)
    """
    __tablename__ = "review_comments"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    scan_run_id = Column(PGUUID(as_uuid=True), ForeignKey("code_scan_runs.id", ondelete="CASCADE"), nullable=False)
    category = Column(String, nullable=False)
    file_path = Column(Text)
    start_line = Column(Integer)
    end_line = Column(Integer)
    comment = Column(Text, nullable=False)
    suggestion = Column(Text)
    confidence = Column(Numeric(4, 3))  # 0.000 ~ 1.000
    meta = Column(JSONB)

    created_at = Column(TIMESTAMP, index=True, comment="생성시간")  # 생성시간
    modified_at = Column(TIMESTAMP, index=True, comment="최종수정시간")  # 최종수정시간
    created_by = Column(String(50), index=True, comment="생성자")  # 생성자
    modified_by = Column(String(50), index=True, comment="최종수정자")  # 최종수정자

    scan_run = relationship("CodeScanRun", back_populates="review_comments")

    __table_args__ = (
        CheckConstraint("category IN ('SECURITY','PERFORMANCE','REFACTOR','TEST','STYLE','OTHER')", name="ck_review_category"),
    )

    def __repr__(self):
        return f"ReviewComment(id={self.id}, category={self.category})"


class ConventionViolation(Base):
    """
    컨벤셔널 규칙 위반 (convention_violations)
    """
    __tablename__ = "convention_violations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    scan_run_id = Column(PGUUID(as_uuid=True), ForeignKey("code_scan_runs.id", ondelete="CASCADE"), nullable=False)
    scope = Column(String, nullable=False)
    key = Column(Text)  # commit hash / rule key
    message = Column(Text, nullable=False)
    details = Column(JSONB)

    created_at = Column(TIMESTAMP, index=True, comment="생성시간")  # 생성시간
    modified_at = Column(TIMESTAMP, index=True, comment="최종수정시간")  # 최종수정시간
    created_by = Column(String(50), index=True, comment="생성자")  # 생성자
    modified_by = Column(String(50), index=True, comment="최종수정자")  # 최종수정자

    scan_run = relationship("CodeScanRun", back_populates="convention_violations")

    __table_args__ = (
        CheckConstraint("scope IN ('COMMITS','CODE_STYLE')", name="ck_conv_scope"),
    )

    def __repr__(self):
        return f"ConventionViolation(id={self.id}, scope={self.scope})"


class LintViolation(Base):
    """
    린트 위반 (lint_violations)
    """
    __tablename__ = "lint_violations"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    scan_run_id = Column(PGUUID(as_uuid=True), ForeignKey("code_scan_runs.id", ondelete="CASCADE"), nullable=False)
    language = Column(String, nullable=False)
    tool = Column(Text)
    file_path = Column(Text)
    line = Column(Integer)
    rule_id = Column(Text)
    severity = Column(Text)
    message = Column(Text)
    meta = Column(JSONB)

    created_at = Column(TIMESTAMP, index=True, comment="생성시간")  # 생성시간
    modified_at = Column(TIMESTAMP, index=True, comment="최종수정시간")  # 최종수정시간
    created_by = Column(String(50), index=True, comment="생성자")  # 생성자
    modified_by = Column(String(50), index=True, comment="최종수정자")  # 최종수정자

    scan_run = relationship("CodeScanRun", back_populates="lint_violations")

    __table_args__ = (
        CheckConstraint("language IN ('cpp','java','python','javascript')", name="ck_lint_language"),
    )

    def __repr__(self):
        return f"LintViolation(id={self.id}, language={self.language}, rule_id={self.rule_id})"


class Artifact(Base):
    """
    산출물 레지스트리 (artifacts)
    """
    __tablename__ = "artifacts"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    scan_run_id = Column(PGUUID(as_uuid=True), ForeignKey("code_scan_runs.id", ondelete="CASCADE"), nullable=False)
    kind = Column(String, nullable=False)  # 'SARIF','MARKDOWN','HTML','RAW','JSON'
    name = Column(Text, nullable=False)
    uri = Column(Text, nullable=False)
    sha256 = Column(Text)
    bytes = Column(BigInteger)

    created_at = Column(TIMESTAMP, index=True, comment="생성시간")  # 생성시간
    modified_at = Column(TIMESTAMP, index=True, comment="최종수정시간")  # 최종수정시간
    created_by = Column(String(50), index=True, comment="생성자")  # 생성자
    modified_by = Column(String(50), index=True, comment="최종수정자")  # 최종수정자

    scan_run = relationship("CodeScanRun", back_populates="artifacts")

    __table_args__ = (
        CheckConstraint("kind IN ('SARIF','MARKDOWN','HTML','RAW','JSON')", name="ck_artifact_kind"),
    )

    def __repr__(self):
        return f"Artifact(id={self.id}, kind={self.kind}, name={self.name})"


# ---- Indexes to match DDL ----
Index('idx_code_scan_runs_repo_started', CodeScanRun.repo_url, desc(CodeScanRun.started_at))
Index('idx_findings_run', Finding.scan_run_id)
Index('idx_findings_sev', Finding.severity)
Index('idx_review_run', ReviewComment.scan_run_id)
Index('idx_conv_run', ConventionViolation.scan_run_id)
Index('idx_lint_run', LintViolation.scan_run_id)
Index('idx_lint_lang', LintViolation.language)
Index('idx_artifact_run', Artifact.scan_run_id)
