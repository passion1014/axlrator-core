from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.base import Checkpoint
import redis
import json

class RedisSaver2(Checkpoint):
    """Redis 기반 체크포인터."""
    def __init__(self, redis_url="redis://localhost:6379", db=0):
        self.redis = redis.StrictRedis.from_url(redis_url, db=db)

    def save_state(self, thread_id: str, state: dict):
        """상태를 Redis에 저장."""
        self.redis.set(thread_id, json.dumps(state))

    def load_state(self, thread_id: str) -> dict:
        """Redis에서 상태를 로드."""
        state = self.redis.get(thread_id)
        if state is None:
            return {}
        return json.loads(state)

    def delete_state(self, thread_id: str):
        """Redis에서 상태 삭제."""
        self.redis.delete(thread_id)

class PosgresqlSaver(Checkpoint):
    """Posgresql 기반 체크포인터."""
    def __init__(self, redis_url="redis://localhost:6379", db=0):
        self.redis = redis.StrictRedis.from_url(redis_url, db=db)

    def save_state(self, thread_id: str, state: dict):
        """상태를 Redis에 저장."""
        self.redis.set(thread_id, json.dumps(state))

    def load_state(self, thread_id: str) -> dict:
        """Redis에서 상태를 로드."""
        state = self.redis.get(thread_id)
        if state is None:
            return {}
        return json.loads(state)

    def delete_state(self, thread_id: str):
        """Redis에서 상태 삭제."""
        self.redis.delete(thread_id)

class HybridSaver(Checkpoint):
    """MemorySaver와 RedisSaver를 결합한 체크포인터."""
    def __init__(self, redis_url="redis://localhost:6379", db=0):
        self.memory_saver = MemorySaver()
        self.redis_saver = PosgresqlSaver(redis_url, db)

    def save_state(self, thread_id: str, state: dict):
        """
        상태를 메모리에 저장하고, 필요 시 Redis에 저장.
        :param thread_id: 상태를 구분할 고유 ID
        :param state: 저장할 상태 데이터
        """
        # 메모리에 우선 저장
        self.memory_saver.save_state(thread_id, state)

    def persist_to_redis(self, thread_id: str):
        """메모리 상태를 Redis에 영구 저장."""
        state = self.memory_saver.load_state(thread_id)
        if state:
            self.redis_saver.save_state(thread_id, state)

    def load_state(self, thread_id: str) -> dict:
        """
        메모리에서 로드, 없으면 Redis에서 로드.
        :param thread_id: 상태를 구분할 고유 ID
        :return: 복원된 상태 데이터
        """
        # 메모리에서 먼저 시도
        state = self.memory_saver.load_state(thread_id)
        if not state:
            # 메모리에 없으면 Redis에서 복원
            state = self.redis_saver.load_state(thread_id)
            if state:
                self.memory_saver.save_state(thread_id, state)
        return state

    def delete_state(self, thread_id: str):
        """메모리와 Redis에서 상태 삭제."""
        self.memory_saver.delete_state(thread_id)
        self.redis_saver.delete_state(thread_id)
