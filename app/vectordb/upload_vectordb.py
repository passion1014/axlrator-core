import os
from langchain.text_splitter import CharacterTextSplitter
from langchain_community.vectorstores import FAISS
import chardet
import argparse

from langchain_text_splitters import RecursiveCharacterTextSplitter
from app.utils import get_embedding_model
from langchain.docstore.document import Document



def load_and_detect_encoding(file_path):
    # 1. 파일 로드 및 인코딩 탐지
    with open(file_path, 'rb') as f:
        raw_data = f.read()
        result = chardet.detect(raw_data)
        file_encoding = result['encoding']
    
    # 파일 읽기
    with open(file_path, 'r', encoding=file_encoding) as file:
        text = file.read()
    return text


# 이건 테스트를 위한 함수. - 사용하지 않음
def vector_upload(file_path, index_name):
    # 파일 내용 로드 및 처리
    text = load_and_detect_encoding(file_path)
    print("파일 내용을 성공적으로 읽었습니다.")

    # 2. 의미별로 chunk로 나누기
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=100, chunk_overlap=5)
    chunks = text_splitter.split_text(text)

    # 각 chunk를 문서 객체로 변환
    docs = text_splitter.create_documents(chunks)
    
    # 각 chunk를 문서 객체로 변환 이 과정에서 각 청크를 개별 문서로 다룬다
    docs = [Document(page_content=chunk) for chunk in chunks]

    # FAISS 인덱스 생성 및 문서 추가
    embeddings = get_embedding_model()
    db = FAISS.from_documents(docs, embeddings)

    # FAISS 인덱스 저장
    vectordb_path = os.path.join(os.path.dirname(__file__), '../..', 'data/vector')
    print('==============' + vectordb_path)
            
    db.save_local(f"{vectordb_path}/{index_name}")
    print(f"FAISS 인덱스를 '{vectordb_path}/{index_name}'에 저장했습니다.")


if __name__ == '__main__':
    ''' 사용법
        # python upload_vectordb.py ../data/norway.txt db_desc
    '''

    # argparse를 사용하여 명령줄 인자 파싱
    parser = argparse.ArgumentParser(description='파일 경로를 입력받아 내용을 처리합니다.')
    parser.add_argument('file_path', type=str, help='처리할 파일의 경로')
    parser.add_argument('index_name', type=str, help='FAISS 인덱스의 이름')
    
    args = parser.parse_args()

    # vector_upload(args.file_path, args.index_name)
