import os
import luigi
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.db_model.database_models import OrgRSrc, ChunkedData  # 정의된 ORM 모델들
from app.utils import get_embedding_model
from datetime import datetime
from app.db_model.database import SessionLocal
import numpy as np  # 임베딩을 위해 numpy 사용
import uuid

from app.vectordb.faiss_vectordb import FaissVectorDB, PostgresDocstore  # 청크 ID를 생성하기 위해 사용


# 임베딩 함수: 예시로 랜덤 벡터 생성
def embed_content(embeddings, content):
    # 텍스트를 임베딩
    embedded_vector = embeddings.embed_documents(content)
    # print(f"### embedded_vector 결과 = {embedded_vector}")
    
    return embedded_vector


# Luigi Task: DB에서 데이터를 읽는 작업
class ReadFromDB(luigi.Task):
    def output(self):
        return luigi.LocalTarget('workflow/working/vector/org_resrc_data.txt')

    def run(self):
        session = SessionLocal()
        
        # OrgRSrc 테이블에서 is_vectorize가 True가 아닌 항목만 조회 (False, None)
        org_resrc_data_list = session.query(OrgRSrc).filter(OrgRSrc.is_vectorize.isnot(True)).all()

        with self.output().open('w') as f:
            for org_resrc in org_resrc_data_list:
                f.write(f"{org_resrc.id}, {org_resrc.resrc_name}, {org_resrc.class_name}, {org_resrc.resrc_desc}\n")

        session.close()

# Luigi Task: 데이터를 읽고 임베딩 생성
class EmbedData(luigi.Task):
    faissVectorDB = FaissVectorDB()

    def requires(self):
        # DB에서 직접 데이터를 읽기 때문에 파일 의존성이 필요 없음
        return None 

    
    def output(self):
        return luigi.LocalTarget('workflow/working/vector/embedded_data.txt')


    def run(self):
        session = SessionLocal()

        # faiss 인덱스 정보 셋팅
        index_name = 'is_modon_proto'
        faiss_index_file_path = f'data/vector/{index_name}.index'

        # FAISS_INFO 저장
        psql_docstore = PostgresDocstore(db_session=session)
        faiss_info = psql_docstore.insert_faiss_info(index_name=index_name, index_desc="프로그램 소스 코드", index_file_path=faiss_index_file_path)

        # OrgRSrc 테이블에서 is_vectorize가 True가 아닌 항목만 조회
        org_resrc_list = session.query(OrgRSrc).filter(OrgRSrc.is_vector.isnot(True)).all()

        
        with self.output().open('w') as output_file:
            for org_resrc in org_resrc_list:

                org_resrc_id = org_resrc.id
                print(f"### org_resrc_id = {org_resrc_id} 시작!")

                # org_resrc_id로 ChunkedData 를 조회
                chunked_data_list = session.query(ChunkedData).filter(ChunkedData.org_resrc_id == org_resrc_id).all()

                # 각각의 ChunkedData에 대해 처리
                for data in chunked_data_list:
                    # FAISS.id 업데이트
                    data.faiss_info_id = faiss_info.id
                    
                    # metadata 생성하여 함께 업데이트 하기
                    data.document_metadata = data.document_metadata or {}

                    # 벡터 인덱스 생성
                    faiss_index = self.faissVectorDB.add_embedded_content_to_index(data.id, data.content, data.document_metadata)
                    data.vector_index = faiss_index # 벡터 인덱스 업데이트

                    # chunked_data의 값 변경 및 수정
                    session.add(data)
                    session.commit()

                    # 파일에 저장
                    output_file.write(f"{data.org_resrc_id}, {data.id}, {data.vector_index}\n")
                
                # OrgRSrc 처리 후 is_vectorize 값을 True로 업데이트
                org_resrc.is_vectorize = True
                session.add(org_resrc)  # OrgRSrc 업데이트 사항 커밋
                session.commit()
                
                print(f"### org_resrc_id = {org_resrc_id}, 함수 갯수 = {len(chunked_data_list)} 끝!")
                

            # FAISS_INFO에 저장 및 .index 파일 생성
            self.faissVectorDB.write_index(file_path=faiss_index_file_path)

        session.close()

# Luigi Task: 전체 파이프라인 실행
class ProcessAllData(luigi.Task):
    def requires(self):
        return EmbedData()

    def output(self):
        return luigi.LocalTarget('workflow/working/vector/all_data_processed.txt')

    def run(self):
        with self.input().open('r') as f:
            data = f.read()

        with self.output().open('w') as f:
            f.write('All data has been processed and embedded.\n')

# Luigi 실행: 프로젝트 실행
if __name__ == "__main__":
    luigi.build([ProcessAllData()], local_scheduler=True)