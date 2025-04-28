from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.base import Checkpoint
# import redis
import json

from axlrator_core.db_model.data_repository import ChatHistoryRepository

# class RedisSaver(Checkpoint):
#     """Redis 기반 체크포인터."""
#     def __init__(self, redis_url="redis://localhost:6379", db=0):
#         self.redis = redis.StrictRedis.from_url(redis_url, db=db)

#     def save_state(self, thread_id: str, state: dict):
#         """상태를 Redis에 저장."""
#         self.redis.set(thread_id, json.dumps(state))

#     def load_state(self, thread_id: str) -> dict:
#         """Redis에서 상태를 로드."""
#         state = self.redis.get(thread_id)
#         if state is None:
#             return {}
#         return json.loads(state)

#     def delete_state(self, thread_id: str):
#         """Redis에서 상태 삭제."""
#         self.redis.delete(thread_id)

class PostgresqlSaver(Checkpoint):
    """Posgresql 기반 체크포인터."""
    def __init__(self, session):
        self.chat_repository = ChatHistoryRepository(session=session)

    def save_state(self, thread_id: str, state: dict):
        # 기존에 있으면 업데이트
        list = self.chat_repository.get_chat_history_by_thread_id(thread_id=thread_id)
        if list:
            # 기존의 채팅 기록이 존재하면 업데이트
            for chat in list:
                chat.data = json.dumps(state)
                chat.title = state.get("title")
                chat.type_code = state.get("type_code")
                chat.user_info_id = state.get("user_info_id")
                self.chat_repository.update_chat_history(chat.id, chat)
            return
        
        chat_history = {
            "thread_id" : thread_id,
            "data" : state,
            "title" : state.get("title"),
            "type_code" : state.get("type_code"),
            "user_info_id" : state.get("user_info_id"),
        }
        self.chat_repository.create_chat_history(chat_history)

    def load_state(self, thread_id: str) -> dict:
        list = self.chat_repository.get_chat_history_by_thread_id(thread_id=thread_id)
        if list is None:
            return {}
        return json.loads(list)

    def delete_state(self, thread_id: str):
        """Redis에서 상태 삭제."""
        # self.redis.delete(thread_id)

class HybridSaver(Checkpoint):
    """MemorySaver와 PosgresqlSaver를 결합한 체크포인터."""
    def __init__(self, session):
        self.memory_saver = MemorySaver()
        self.postgresql_saver = PostgresqlSaver(session)

    def save_state(self, thread_id: str, state: dict):
        """
        상태를 메모리에 저장하고, 필요 시 Redis에 저장.
        :param thread_id: 상태를 구분할 고유 ID
        :param state: 저장할 상태 데이터
        """
        # 메모리에 우선 저장
        self.memory_saver.save_state(thread_id, state)

    def persist_to_db(self, thread_id: str):
        """메모리 상태를 Redis에 영구 저장."""
        state = self.memory_saver.load_state(thread_id)
        if state:
            self.postgresql_saver.save_state(thread_id, state)

    def load_state(self, thread_id: str) -> dict:
        """
        메모리에서 로드, 없으면 DB에서 로드.
        :param thread_id: 상태를 구분할 고유 ID
        :return: 복원된 상태 데이터
        """
        # 메모리에서 먼저 시도
        state = self.memory_saver.load_state(thread_id)
        if not state:
            # 메모리에 없으면 DB에서 복원
            state = self.postgresql_saver.load_state(thread_id)
            if state:
                self.memory_saver.save_state(thread_id, state)
        return state

    def delete_state(self, thread_id: str):
        """메모리와 DB에서 상태 삭제."""
        self.memory_saver.delete_state(thread_id)
        self.postgresql_saver.delete_state(thread_id)
