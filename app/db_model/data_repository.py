

import os
from app.db_model.database_models import ChunkedData, OrgRSrc


class OrgRSrcRepository:
    def __init__(self, session):
        """
        OrgRSrcRepository 초기화
        
        Args:
            session: SQLAlchemy 세션 객체
        """
        self.session = session


    def create_org_resrc(self, file_path: str, type: str = '99', desc:str = '-') -> OrgRSrc:
        """
        원본 리소스 정보를 생성하고 저장합니다.
        
        Args:
            file_path: 파일 경로
            
        Returns:
            생성된 OrgRSrc 객체
        """
        # 원본 파일 정보 저장
        org_resrc = OrgRSrc(
            resrc_name = os.path.basename(file_path),  # 파일명
            resrc_type = type,
            resrc_path = file_path,
            resrc_desc = desc,
            # last_modified_time = class_info.get('last_modified'), # 추후 어떤 값을 셋팅 할지 확인 필요
        )
        self.session.add(org_resrc)
        self.session.flush() # org_resrc.id를 얻기 위해 flush를 한다. but commit 되기 전임
        
        return org_resrc
    
    
    def commit(self):
        """
        세션의 변경사항을 데이터베이스에 커밋합니다.
        """
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

class ChunkedDataRepository:
    def __init__(self, session):
        """
        ChunkedDataRepository 초기화
        
        Args:
            session: SQLAlchemy 세션 객체
        """
        self.session = session

    def create_chunked_data(self, org_resrc_id: int, seq: int, data_name: str
                            , data_type: str, content: str, context_chunk: str
                            , document_metadata: dict) -> ChunkedData:
        chunked_data = ChunkedData(
            seq = seq,
            org_resrc_id = org_resrc_id,
            data_name = data_name,
            data_type = data_type, 
            content = content,
            context_chunk = context_chunk,
            document_metadata = document_metadata
        )
        self.session.add(chunked_data)
        self.session.flush()
        
        return chunked_data

    def commit(self):
        """
        세션의 변경사항을 데이터베이스에 커밋합니다.
        """
        try:
            self.session.commit()
        except Exception as e:
            self.session.rollback()
            raise e

