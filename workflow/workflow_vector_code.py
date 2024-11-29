from app.db_model.data_repository import OrgRSrcRepository
from app.process.vectorize_process import process_vectorize
import luigi
from datetime import datetime
from app.db_model.database import SessionLocal
from app.vectordb.faiss_vectordb import FaissVectorDB  # 청크 ID를 생성하기 위해 사용

# 임베딩 함수: 예시로 랜덤 벡터 생성
def embed_content(embeddings, content):
    # 텍스트를 임베딩
    embedded_vector = embeddings.embed_documents(content)
    
    return embedded_vector


# Luigi Task: 데이터를 읽고 임베딩 생성
class EmbedData(luigi.Task):
    timestamp = luigi.Parameter(default=datetime.now().strftime('%Y%m%d%H%M%S'))  # 타임스탬프 생성
    index_name = luigi.Parameter()  # 중간 디렉토리 경로 전달

    def requires(self):
        # DB에서 직접 데이터를 읽기 때문에 파일 의존성이 필요 없음
        return None 

    def output(self):
        return luigi.LocalTarget(f'workflow/working/vector/embedded_data_{self.timestamp}.txt')

    def run(self):
        print(f"####### index_name={self.index_name}")
        
        session = SessionLocal()
        faiss_vector_db = FaissVectorDB(db_session=session, index_name=self.index_name)
        orgrsrc_repository = OrgRSrcRepository(session=session)

        faiss_info = faiss_vector_db.psql_docstore.get_faiss_info()
        if faiss_info is None:
            raise Exception(f"# 기저장된 {self.index_name}의 FAISS 정보가 없습니다. 생성이 필요합니다.")

        # index_name에 따라 resrc_type 설정 (임시처리)
        if self.index_name == 'cg_code_assist':
            resrc_type = '01'
        elif self.index_name == 'cg_text_to_sql':
            resrc_type = '02'
        else:
            resrc_type = '99'

        # OrgRSrc 테이블에서 is_vector가 True가 아닌 항목만 조회
        # org_resrc_list = session.query(OrgRSrc).filter(OrgRSrc.is_vector.isnot(True)).all()
        org_resrc_list = orgrsrc_repository.get_org_resrc(is_vector=False, resrc_type=resrc_type)
        for org_resrc in org_resrc_list:

            # 벡터화
            process_vectorize(index_name=self.index_name, session=session, org_resrc=org_resrc, faiss_info=faiss_info)


        session.close()

# Luigi Task: 전체 파이프라인 실행
class ProcessAllData(luigi.Task):
    index_name = luigi.Parameter()
    
    def requires(self):
        return EmbedData(index_name=self.index_name)

    def output(self):
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        return luigi.LocalTarget(f'workflow/working/vector/all_data_processed_{timestamp}.txt')


    def run(self):
        with self.input().open('r') as f:
            data = f.read()

        with self.output().open('w') as f:
            f.write('모든 데이터의 작업이 완료 됨.\n')

# Luigi 실행: 프로젝트 실행
if __name__ == "__main__":
    luigi.build([ProcessAllData(index_name="cg_code_assist")], local_scheduler=True, log_level='DEBUG')

# 실행방법
# export PYTHONPATH=$PYTHONPATH:/app/rag_server
# luigi --module workflow.workflow_vector_code ProcessAllData --local-scheduler
