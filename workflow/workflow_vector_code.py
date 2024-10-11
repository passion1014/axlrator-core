import luigi
from app.db_model.database_models import OrgRSrc, ChunkedData  # 정의된 ORM 모델들
from datetime import datetime, time
from app.db_model.database import SessionLocal
from app.vectordb.faiss_vectordb import FaissVectorDB, PostgresDocstore  # 청크 ID를 생성하기 위해 사용

# 임베딩 함수: 예시로 랜덤 벡터 생성
def embed_content(embeddings, content):
    # 텍스트를 임베딩
    embedded_vector = embeddings.embed_documents(content)
    # print(f"### embedded_vector 결과 = {embedded_vector}")
    
    return embedded_vector


# Luigi Task: 데이터를 읽고 임베딩 생성
class EmbedData(luigi.Task):
    timestamp = luigi.Parameter(default=datetime.now().strftime('%Y%m%d%H%M%S'))  # 타임스탬프 생성
    faissVectorDB = FaissVectorDB()

    def requires(self):
        # DB에서 직접 데이터를 읽기 때문에 파일 의존성이 필요 없음
        return None 

    
    def output(self):
        
        return luigi.LocalTarget(f'workflow/working/vector/embedded_data_{self.timestamp}.txt')


    def run(self):
        session = SessionLocal()

        # faiss 인덱스 정보 셋팅 (추후 별도 관리하도록 수정 필요)
        index_name = 'cg_text_to_sql' #'cg_code_assist'
        faiss_index_file_path = f'data/vector/{index_name}.index'

        # FAISS_INFO 저장 (있으면 조회)
        psql_docstore = PostgresDocstore(db_session=session)
        
        faiss_info = psql_docstore.get_faiss_info(index_name=index_name)
        if faiss_info is None:
            print(f"-------------------- {index_name}에 대한 FAISS 정보가 없습니다. 새로 생성합니다.")
            faiss_info = psql_docstore.insert_faiss_info(index_name=index_name, index_desc="프로그램 소스 코드", index_file_path=faiss_index_file_path)
        else:
            print(f"-------------------- {index_name}에 대한 FAISS 정보가 이미 존재합니다.")

        # OrgRSrc 테이블에서 is_vector가 True가 아닌 항목만 조회
        org_resrc_list = session.query(OrgRSrc).filter(OrgRSrc.is_vector.isnot(True)).all()
        print(f"-------------------- org_resrc_list = {org_resrc_list}")
        
        with self.output().open('w') as output_file:
            for org_resrc in org_resrc_list:

                org_resrc_id = org_resrc.id
                print(f"-------------------- org_resrc_id = {org_resrc_id} 시작!")

                # org_resrc_id로 ChunkedData 를 조회
                chunked_data_list = session.query(ChunkedData).filter(ChunkedData.org_resrc_id == org_resrc_id).all()

                # 각각의 ChunkedData에 대해 처리
                for data in chunked_data_list:
                    # FAISS.id 업데이트
                    data.faiss_info_id = faiss_info.id
                    
                    # metadata 생성하여 함께 업데이트 하기
                    data.document_metadata = data.document_metadata or {}

                    # document_metadata가 딕셔너리인지 확인
                    if not isinstance(data.document_metadata, dict):
                        print(f"-------------------- 경고: document_metadata가 딕셔너리가 아닙니다. 빈 딕셔너리로 초기화합니다. 타입 = {type(data)}")
                        data.document_metadata = {}

                    try:
                        # 벡터 인덱스 생성
                        faiss_index = self.faissVectorDB.add_embedded_content_to_index(data.id, data.content, data.document_metadata)
                        data.vector_index = faiss_index # 벡터 인덱스 업데이트
                        data.modified_at = datetime.now()
                        data.modified_by = "vector_workflow"

                        # chunked_data의 값 변경 및 수정
                        session.add(data)
                        session.commit()

                        # 파일에 저장
                        output_file.write(f"{data.org_resrc_id}, {data.id}, {data.vector_index}\n")
                    except Exception as e:
                        print(f"-------------------- 오류 발생: {e}")
                        session.rollback()
                
                # OrgRSrc 처리 후 is_vectorize 값을 True로 업데이트
                # org_resrc.is_vector = True # 임시 주석
                org_resrc.modified_at = datetime.now()
                org_resrc.modified_by = "vector_workflow"
                session.add(org_resrc)  # OrgRSrc 업데이트 사항 커밋
                session.commit()
                
                print(f"-------------------- org_resrc_id = {org_resrc_id}, 함수 갯수 = {len(chunked_data_list)} 끝!")

            # FAISS_INFO에 저장 및 .index 파일 생성
            self.faissVectorDB.write_index(file_path=faiss_index_file_path)

        session.close()

# Luigi Task: 전체 파이프라인 실행
class ProcessAllData(luigi.Task):
    def requires(self):
        return EmbedData()

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
    luigi.build([ProcessAllData()], local_scheduler=True, log_level='DEBUG')

# 실행방법
# export PYTHONPATH=$PYTHONPATH:/app/rag_server
# luigi --module workflow.workflow_vector_code ProcessAllData --local-scheduler
