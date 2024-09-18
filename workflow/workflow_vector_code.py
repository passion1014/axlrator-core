import os
import luigi
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from app.db_model.database_models import OrgRSrc, OrgRSrcData, VectorData, VectorDataChunk  # 정의된 ORM 모델들
from app.utils import get_embedding_model
from datetime import datetime
from app.db_model.database import SessionLocal
import numpy as np  # 임베딩을 위해 numpy 사용
import uuid

from app.vectordb.faiss_vectordb import FaissVectorDB  # 청크 ID를 생성하기 위해 사용


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
    # 임베딩 모델 가져오기
    # embeddings = get_embedding_model()
    faissVectorDB = FaissVectorDB()

    def requires(self):
        # DB에서 직접 데이터를 읽기 때문에 파일 의존성이 필요 없음
        return None 

    
    def output(self):
        return luigi.LocalTarget('workflow/working/vector/embedded_data.txt')


    def run(self):
        session = SessionLocal()

        # OrgRSrc 테이블에서 is_vectorize가 True가 아닌 항목만 조회
        org_resrc_list = session.query(OrgRSrc).filter(OrgRSrc.is_vector.isnot(True)).all()

        with self.output().open('w') as output_file:
            for org_resrc in org_resrc_list:

                org_resrc_id = org_resrc.id
                print(f"### org_resrc_id = {org_resrc_id} 시작!")

                # org_resrc_id로 OrgRSrcData 를 조회
                org_resrc_data = session.query(OrgRSrcData).filter(OrgRSrcData.org_resrc_id == org_resrc_id).all()

                # 각각의 OrgRSrcData에 대해 처리
                for data in org_resrc_data:
                    # 데이터 임베딩
                    # embedding_data = embed_content(self.embeddings, data.content)
                    
                    # TODO
                    # 1) FAISS index 확인
                    # 2) OrgRSrcData 업데이트
                    # 3) metadata 생성하여 함께 업데이트 하기
                    
                    self.faissVectorDB.add_document_to_store(data.id, )
                    self.faissVectorDB.write_index(file_path='data/vector/faiss_test.index')
                    

                    '''
                    # 벡터 데이터를 DB에 저장
                    vector_data = VectorData(
                        org_resrc_id=org_resrc_id,
                        proc_time=datetime.now().time()
                    )
                    session.add(vector_data)

                    # 임베딩 벡터를 여러 청크로 나눠서 저장
                    # chunk_id = uuid.uuid4()
                    vector_chunk = VectorDataChunk(
                        vector_data_id=vector_data.id,
                        org_resrc_id=org_resrc_id,
                        # chunk_id=chunk_id,
                        chunk_data=str(embedding_data)  # 문자열로 저장
                    )
                    session.add(vector_chunk)
                    '''

                    # 파일에 저장
                    output_file.write(f"{org_resrc_id}, {vector_data.id}, {embedding_data}\n")
                
                # OrgRSrc 처리 후 is_vectorize 값을 True로 업데이트
                org_resrc.is_vectorize = True
                session.add(org_resrc)  # OrgRSrc 업데이트 사항 커밋
                session.commit()
                
                print(f"### org_resrc_id = {org_resrc_id}, 함수 갯수 = {len(org_resrc_data)} 끝!")

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