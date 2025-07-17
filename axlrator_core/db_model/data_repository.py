from datetime import datetime
import os
from typing import List

from sqlalchemy import desc, select, update, delete
from sqlalchemy.orm import joinedload
from sqlalchemy.ext.asyncio import AsyncSession
from axlrator_core.db_model.database_models import ChatHistory, ChunkedData, FaissInfo, OrgRSrc, RSrcTable, RSrcTableColumn, UserInfo

class FaissInfoRepository:
    def __init__(self, session):
        self.session = session
    
    async def get_faiss_by_id(self, faiss_info_id: int) -> 'FaissInfo':
        """
        ID로 FAISS 정보를 조회합니다.
        """
        stmt = select(FaissInfo).where(FaissInfo.id == faiss_info_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()


    async def get_faisses(self, index_id: int = None, index_name: str = None) -> List['FaissInfo']:
        """
        ID 또는 이름으로 FAISS 정보를 조회합니다.
        """
        stmt = select(FaissInfo)
        
        if index_id is not None:
            stmt = stmt.where(FaissInfo.id == index_id)
        
        if index_name is not None:
            stmt = stmt.where(FaissInfo.index_name.like(f"%{index_name}%"))
        
        result = await self.session.execute(stmt)
        return result.scalars().all()


    async def get_faiss_datas(self, index_name: str, from_date: datetime, to_date: datetime, data_name: str, data_type: str) -> List:
        """
        FAISS 정보와 관련된 ChunkedData를 조회합니다.
        """
        stmt = select(FaissInfo, ChunkedData).join(ChunkedData, FaissInfo.id == ChunkedData.faiss_info_id)
        
        if index_name is not None:
            stmt = stmt.where(FaissInfo.index_name.like(f"%{index_name}%"))
        
        if from_date is not None and to_date is not None:
            stmt = stmt.where(ChunkedData.created_at.between(from_date, to_date))
        
        if data_name is not None:
            stmt = stmt.where(ChunkedData.data_name.like(f"{data_name}%"))
        
        if data_type is not None:
            stmt = stmt.where(ChunkedData.data_type == data_type)
        
        result = await self.session.execute(stmt)
        
        faiss_data_list = []
        for faiss_info, chunked_data in result.all():
            faiss_data_list.append({
                'faiss_info': faiss_info.to_dict(),
                'chunked_data': chunked_data.to_dict()
            })
        
        return faiss_data_list



class OrgRSrcRepository:
    def __init__(self, session):
        """
        OrgRSrcRepository 초기화
        
        Args:
            session: SQLAlchemy 세션 객체
        """
        self.session = session

    async def get_org_resrc_by_id(self, org_resrc_id: int) -> OrgRSrc:
        """
        ID로 원본 리소스 정보를 조회합니다.
        
        Args:
            org_resrc_id: 조회할 원본 리소스 ID
            
        Returns:
            조회된 OrgRSrc 객체. 없으면 None 반환
        """
        stmt = select(OrgRSrc).where(OrgRSrc.id == org_resrc_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def aget_org_resrc(self, resrc_name: str = None, resrc_type: str = None, 
                            resrc_path: str = None, resrc_desc: str = None, 
                            is_vector: bool = None) -> list[OrgRSrc] | OrgRSrc:
        stmt = select(OrgRSrc)
        
        # 각 파라미터가 있는 경우에만 필터 조건 추가
        if resrc_name is not None:
            stmt = stmt.where(OrgRSrc.resrc_name == resrc_name)
            
        if resrc_type is not None:
            stmt = stmt.where(OrgRSrc.resrc_type == resrc_type)
            
        if resrc_path is not None:
            stmt = stmt.where(OrgRSrc.resrc_path == resrc_path)
            
        if resrc_desc is not None:
            stmt = stmt.where(OrgRSrc.resrc_desc == resrc_desc)
            
        if is_vector is not None:
            stmt = stmt.where(OrgRSrc.is_vector == is_vector)
            
        # 모든 결과 반환
        result = await self.session.execute(stmt)
        return result.scalars().all()

    def get_org_resrc(self, resrc_name: str = None, resrc_type: str = None, 
                            resrc_path: str = None, resrc_desc: str = None, 
                            is_vector: bool = None) -> list[OrgRSrc] | OrgRSrc:
        stmt = select(OrgRSrc)
        
        # 각 파라미터가 있는 경우에만 필터 조건 추가
        if resrc_name is not None:
            stmt = stmt.where(OrgRSrc.resrc_name == resrc_name)
            
        if resrc_type is not None:
            stmt = stmt.where(OrgRSrc.resrc_type == resrc_type)
            
        if resrc_path is not None:
            stmt = stmt.where(OrgRSrc.resrc_path == resrc_path)
            
        if resrc_desc is not None:
            stmt = stmt.where(OrgRSrc.resrc_desc == resrc_desc)
            
        if is_vector is not None:
            stmt = stmt.where(OrgRSrc.is_vector == is_vector)
            
        # 모든 결과 반환
        result = self.session.execute(stmt)
        return result.scalars().all()

    async def acreate_org_resrc(self, file_path: str, type: str = '99', desc:str = '-', created_by = '', modified_by = '') -> OrgRSrc:
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
            created_at = datetime.now(),
            created_by = created_by,
            modified_at = datetime.now(),
            modified_by = modified_by
        )
        self.session.add(org_resrc)
        await self.session.flush() # org_resrc.id를 얻기 위해 flush를 한다. but commit 되기 전임
        
        return org_resrc


    async def create_org_resrc(self, file_path: str, type: str = '99', desc: str = '-', created_by='', modified_by='') -> OrgRSrc:
        """
        원본 리소스 정보를 생성하고 저장합니다.

        Args:
            file_path: 파일 경로

        Returns:
            생성된 OrgRSrc 객체
        """
        # 원본 파일 정보 저장
        org_resrc = OrgRSrc(
            resrc_name=os.path.basename(file_path),  # 파일명
            resrc_type=type,
            resrc_path=file_path,
            resrc_desc=desc,
            created_at=datetime.now(),
            created_by=created_by,
            modified_at=datetime.now(),
            modified_by=modified_by
        )

        self.session.add(org_resrc)
        await self.session.flush()  # org_resrc.id를 얻기 위해 flush 수행

        return org_resrc


    async def update_org_resrc(
        self, 
        org_resrc_id: int = 0, 
        resrc_name: str = None, resrc_type: str = None, resrc_path: str = None, resrc_desc: str = None, 
        is_vector: bool = None, modified_by: str = '', org_resrc: OrgRSrc = None
    ) -> OrgRSrc:
        """
        원본 리소스 정보를 업데이트합니다.
        
        Args:
            org_resrc_id: 업데이트할 원본 리소스 ID
            resrc_name: 리소스 이름 (선택)
            resrc_type: 리소스 타입 (선택) 
            resrc_path: 리소스 경로 (선택)
            resrc_desc: 리소스 설명 (선택)
            is_vector: 벡터화 여부 (선택)
            modified_by: 수정자 (선택)
            org_resrc: OrgRSrc 객체 (선택)
            
        Returns:
            업데이트된 OrgRSrc 객체
        """
        if org_resrc is None:
            stmt = select(OrgRSrc).where(OrgRSrc.id == org_resrc_id)
            result = await self.session.execute(stmt)
            org_resrc = result.scalar_one_or_none()
            if not org_resrc:
                raise ValueError(f"ID {org_resrc_id}에 해당하는 원본 리소스를 찾을 수 없습니다.")
            
        if resrc_name is not None:
            org_resrc.resrc_name = resrc_name
        if resrc_type is not None:
            org_resrc.resrc_type = resrc_type
        if resrc_path is not None:
            org_resrc.resrc_path = resrc_path
        if resrc_desc is not None:
            org_resrc.resrc_desc = resrc_desc
        if is_vector is not None:
            org_resrc.is_vector = is_vector
            
        org_resrc.modified_at = datetime.now()
        org_resrc.modified_by = modified_by
        
        self.session.add(org_resrc)
        await self.session.flush()
        
        return org_resrc
    
    async def commit(self):
        """
        세션의 변경사항을 데이터베이스에 커밋합니다.
        """
        try:
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            raise e

class ChunkedDataRepository:
    def __init__(self, session):
        """
        ChunkedDataRepository 초기화
        
        Args:
            session: SQLAlchemy 세션 객체
        """
        self.session = session
        
    async def get_chunked_data_by_faiss_info_id(self, faiss_info_id: int) -> list[ChunkedData]:
        """
        FAISS 정보 ID로 ChunkedData 목록을 조회합니다.
        
        Args:
            faiss_info_id: FAISS 정보 ID
            
        Returns:
            list[ChunkedData]: ChunkedData 목록
        """
        stmt = select(ChunkedData).where(ChunkedData.faiss_info_id == faiss_info_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    
    async def get_chunked_data_by_org_resrc_id(self, org_resrc_id: int) -> list[ChunkedData]:
        """
        원본 리소스 ID로 ChunkedData 목록을 조회합니다.
        """
        stmt = select(ChunkedData).where(ChunkedData.org_resrc_id == org_resrc_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_chunked_data_by_content(self, data_type:str, content: str) -> list[ChunkedData]:
        """
        content를 포함하는 ChunkedData 목록을 조회합니다.
        """
        stmt = select(ChunkedData).where(ChunkedData.content.like(f'%{content}%'))
        if data_type:
            stmt = stmt.where(ChunkedData.data_type == data_type)
            
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_chunked_data_by_id(self, id: str) -> ChunkedData:
        """
        content를 포함하는 ChunkedData 목록을 조회합니다.
        """
        stmt = select(ChunkedData).where(ChunkedData.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()
    
    async def get_by_resrc_id_and_chunk_id(self, org_resrc_id:int, id:int) -> ChunkedData:
        """
        content를 포함하는 ChunkedData 목록을 조회합니다.
        """
        stmt = select(ChunkedData).where(ChunkedData.org_resrc_id == org_resrc_id, ChunkedData.id == id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_chunked_data(
        self, 
        seq: int, 
        org_resrc_id: int, 
        data_name: str, 
        data_type: str, 
        content: str, 
        context_chunk: str, 
        document_metadata: dict, 
        created_by = '', 
        modified_by = ''
    ) -> ChunkedData:
        chunked_data = ChunkedData(
            seq = seq,
            org_resrc_id = org_resrc_id,
            data_name = data_name,
            data_type = data_type, 
            content = content,
            context_chunk = context_chunk,
            document_metadata = document_metadata,
            created_at = datetime.now(),
            created_by = created_by,
            modified_at = datetime.now(),
            modified_by = modified_by
        )
        self.session.add(chunked_data)
        await self.session.flush()
        
        return chunked_data

    async def update_chunked_data(
        self, chunked_data_id: int = None, chunked_data: ChunkedData = None, seq: int = None, 
        org_resrc_id: int = None, data_name: str = None, data_type: str = None, 
        content: str = None, context_chunk: str = None, document_metadata: dict = None, 
        faiss_info_id: int = None, vector_index: int = None, modified_by: str = ''
    ) -> ChunkedData:
        """
        ChunkedData를 업데이트합니다.
        
        Args:
            chunked_data_id: 업데이트할 ChunkedData의 ID
            chunked_data: 업데이트할 ChunkedData 객체
            seq: 순번 
            org_resrc_id: 원본 리소스 ID
            data_name: 데이터명
            data_type: 데이터 유형
            content: 콘텐츠
            context_chunk: 컨텍스트 청크
            document_metadata: 문서 메타데이터
            faiss_info_id: FAISS 정보 ID
            vector_index: 벡터 인덱스
            modified_by: 수정자
            
        Returns:
            업데이트된 ChunkedData 객체
        """
        if chunked_data is None:
            if chunked_data_id is None:
                raise ValueError("chunked_data 또는 chunked_data_id 중 하나는 필수입니다.")
            stmt = select(ChunkedData).where(ChunkedData.id == chunked_data_id)
            result = await self.session.execute(stmt)
            chunked_data = result.scalar_one_or_none()
            if not chunked_data:
                raise ValueError(f"ID가 {chunked_data_id}인 ChunkedData를 찾을 수 없습니다.")
            
        if seq is not None:
            chunked_data.seq = seq
        if org_resrc_id is not None:
            chunked_data.org_resrc_id = org_resrc_id
        if data_name is not None:
            chunked_data.data_name = data_name
        if data_type is not None:
            chunked_data.data_type = data_type
        if content is not None:
            chunked_data.content = content
        if context_chunk is not None:
            chunked_data.context_chunk = context_chunk
        if document_metadata is not None:
            chunked_data.document_metadata = document_metadata
        if faiss_info_id is not None:
            chunked_data.faiss_info_id = faiss_info_id
        if vector_index is not None:
            chunked_data.vector_index = vector_index
            
        chunked_data.modified_at = datetime.now()
        chunked_data.modified_by = modified_by
        
        self.session.add(chunked_data)
        await self.session.flush()
        
        return chunked_data

    async def commit(self):
        """
        세션의 변경사항을 데이터베이스에 커밋합니다.
        """
        try:
            await self.session.commit()
        except Exception as e:
            await self.session.rollback()
            raise e


class RSrcTableRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
        
    # @classmethod
    # async def create(cls, session: AsyncSession) -> 'RSrcTableRepository':
    #     instance = cls()
    #     return instance

    async def get_data_by_table_name(self, table_name: str) -> list[RSrcTable]:
        stmt = select(RSrcTable).where(RSrcTable.table_name == table_name)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    
class RSrcTableColumnRepository:
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def get_data_by_table_id(self, rsrc_table_id: int) -> list[RSrcTable]:
        stmt = select(RSrcTableColumn).where(RSrcTableColumn.rsrc_table_id == rsrc_table_id)
        result = await self.session.execute(stmt)
        return result.scalars().all()
    


class UserInfoRepository:
    def __init__(self, session):
        self.session = session

    async def get_user_by_id(self, user_id: str) -> UserInfo:
        stmt = select(UserInfo).where(UserInfo.user_id == user_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_by_email(self, email: str) -> UserInfo:
        stmt = select(UserInfo).where(UserInfo.email == email)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all_users(self) -> List[UserInfo]:
        stmt = select(UserInfo)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_user(self, user_info: UserInfo) -> UserInfo:
        self.session.add(user_info)
        await self.session.commit()
        return user_info

    async def update_user(self, user_id: str, user_data: dict) -> UserInfo:
        stmt = select(UserInfo).where(UserInfo.user_id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            for key, value in user_data.items():
                setattr(user, key, value)
            await self.session.commit()
        return user

    async def delete_user(self, user_id: str):
        stmt = select(UserInfo).where(UserInfo.user_id == user_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()
        if user:
            await self.session.delete(user)
            await self.session.commit()

class ChatHistoryRepository:
    def __init__(self, session):
        self.session = session

    # async def get_chat_history_by_user_id(self, user_id: str) -> List[ChatHistory]:
    #     stmt = select(ChatHistory).join(UserInfo).where(UserInfo.user_id == user_id)
    #     result = await self.session.execute(stmt)
    #     return result.scalars().all()

    async def get_chat_history_by_user_id_and_type_code(self, user_id: str, type_code: str) -> List[ChatHistory]:
        stmt = select(ChatHistory).join(UserInfo).where(UserInfo.user_id == user_id, ChatHistory.type_code == type_code).order_by(desc(ChatHistory.created_at))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_chat_history_by_title(self, title: str) -> List[ChatHistory]:
        stmt = select(ChatHistory).where(ChatHistory.title == title).order_by(desc(ChatHistory.created_at))
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def create_chat_history(self, chat_data: dict) -> ChatHistory:
        new_chat = ChatHistory(**chat_data)
        self.session.add(new_chat)
        await self.session.commit()
        return new_chat

    async def update_chat_history(self, chat_id: int, chat_data: dict) -> ChatHistory:
        stmt = select(ChatHistory).where(ChatHistory.id == chat_id)
        result = await self.session.execute(stmt)
        chat = result.scalar_one_or_none()
        if chat:
            for key, value in chat_data.items():
                setattr(chat, key, value)
            await self.session.commit()
        return chat

    async def delete_chat_history(self, chat_id: int, user_info_id: int):
        stmt = select(ChatHistory).where(ChatHistory.id == chat_id, ChatHistory.user_info_id == user_info_id)
        result = await self.session.execute(stmt)
        chat = result.scalar_one_or_none()
        if chat:
            await self.session.delete(chat)
            await self.session.commit()

    async def delete_all_chat_history(self, user_info_id: int):
        stmt = select(ChatHistory).where(ChatHistory.user_info_id == user_info_id)
        result = await self.session.execute(stmt)
        chats = result.scalars().all()
        if chats:
            for chat in chats:
                await self.session.delete(chat)
            await self.session.commit()
