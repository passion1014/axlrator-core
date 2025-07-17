from datetime import datetime
import json
import re
import time
import uuid

from typing import Annotated, List, Optional, Sequence, TypedDict

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool

from langfuse import Langfuse
from langfuse.callback import CallbackHandler

from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages
from langgraph.types import StreamWriter

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm.attributes import flag_modified

from axlrator_core.db_model.axlrui_database import get_axlr_session
from axlrator_core.db_model.axlrui_database_models import Chat
from axlrator_core.utils import get_llm_model
from axlrator_core.vectordb.bm25_search import ElasticsearchBM25
from axlrator_core.vectordb.vector_store import get_vector_store



class CodeChatState(TypedDict):
    """The state of the agent."""
    thread_id: str
    chat_type:str # 01: 검색어 찾기, 02: 질문하기, 03: 후속질문하기, 04: 제목짓기, 05: 태그 추출
    messages: Annotated[Sequence[BaseMessage], add_messages] # add_messages is a reducer
    context_datas: Optional[List[dict]] = None # file_contexts, files, vectordatas를 모은 context 데이터 리스트
    context:str
    metadata:Optional[dict] = None
    response:str
    

class CodeChatAgent:
    def __init__(self, index_name:str="cg_code_assist"):
        self.index_name = index_name
        self.langfuse = Langfuse()
        
    @classmethod
    async def create(cls, index_name: str, session: AsyncSession, config) -> 'CodeChatAgent':
        # __init__ 호출
        instance = cls(index_name)
        
        instance.db_session = session
        # instance.faissVectorDB = await get_vector_db(collection_name=index_name, session=session)
        # instance.es_bm25 = ElasticsearchBM25(index_name=index_name)
        
        instance.callback_handlers = config.get("callbacks")
        instance.model = get_llm_model()
        # instance.model = get_llm_model().with_config(callbacks=[callback_handler])
        
        
        return instance


    @staticmethod
    def get_last_user_message(state: CodeChatState) -> Optional[str]:
        """
        Retrieves the last message from the user (HumanMessage) in the chat history.
        
        Returns:
            The content of the last HumanMessage, or None if not found.
        """
        for msg in reversed(state["messages"]):
            if isinstance(msg, HumanMessage):
                return msg.content.strip()
        return None

    @staticmethod
    def format_chat_history(state: CodeChatState) -> str:
        """
        Formats the chat history for display, ensuring proper indentation and separation.
        """
        chat_lines = []
        indent = "  "
        for msg in state["messages"]:
            if isinstance(msg, HumanMessage):
                chat_lines.append(f"{indent}USER: {msg.content.strip()}")
            elif isinstance(msg, AIMessage):
                chat_lines.append(f"{indent}ASSISTANT: {msg.content.strip()}")
        # Join messages with a blank line for separation
        chat_history = "<chat_history>\n" + "\n\n".join(chat_lines) + "\n</chat_history>"
        return chat_history

    def pre_process_node(self, state: CodeChatState) -> CodeChatState:
        # context_datas의 항목중에서 type이 files인 항목들은 content를 조회해서 셋팅한다.
        context_datas = state.get("context_datas", [])
        for i, file in enumerate(context_datas):
            if file.get("type") == "file":
                file_data = self.get_file_context(file["id"])  # file db에서 조회
                if file_data:
                    file["content"] = file_data.get("content", "").strip() or ""  # 조회된 content 셋팅
        
        state["context_datas"] = context_datas
        return state


    def merge_context_datas_node(self, state: CodeChatState) -> CodeChatState:
        parts = []
        context_datas = state.get("context_datas", [])
        
        if isinstance(context_datas, list):
            for i, context_data in enumerate(context_datas):
                if context_data:
                    _content = context_data.get("content", "")
                    if _content.strip():
                        parts.append(
                            f"<source id=\"{i+1}\" name=\"{context_data['name']}\">\n{_content}\n</source>"
                            # id= 셋팅되는 값을 별도의 seq로 관리하는게 좋을듯.
                        )

        if parts:
            content = "\n\n".join(parts)
            state["context"] = content
        
        return state

    def get_file_context(self, file_id: str) -> Optional[dict]:
        from axlrator_core.db_model.axlrui_database import get_axlr_session
        from axlrator_core.db_model.axlrui_database_models import File

        with get_axlr_session() as session:
            file_row = session.query(File).filter(File.id == file_id).first()
            if file_row and file_row.data:
                try:
                    # content가 문자열인지 확인하고, 인코딩 문제 예방을 위한 보정
                    data = file_row.data
                    if isinstance(data, str):
                        data = json.loads(data)

                    if isinstance(data, bytes):
                        data = json.loads(data.decode("utf-8", errors="replace"))

                    elif not isinstance(data, dict):
                        data = {}

                    return data
                except Exception as e:
                    # 로깅을 추가하고 None 반환
                    print(f"Error parsing file data: {e}")
                    return None
        return None


    @tool
    def get_weather(self, location: str):
        """Call to get the weather from a specific location."""
        if any([city in location.lower() for city in ["sf", "san francisco"]]):
            return "It's sunny in San Francisco, but you better look out if you're a Gemini 😈."
        else:
            return f"I am not sure what the weather is in {location}"


    # Define our tool node
    def tool_node(self, state: CodeChatState):
        tools = [self.get_weather]
        tools_by_name = {tool.name: tool for tool in tools}

        outputs = []
        for tool_call in state["messages"][-1].tool_calls:
            tool_result = tools_by_name[tool_call["name"]].invoke(tool_call["args"])
            outputs.append(
                ToolMessage(
                    content=json.dumps(tool_result),
                    name=tool_call["name"],
                    tool_call_id=tool_call["id"],
                )
            )
        return {"messages": outputs}

    @staticmethod
    def convert_to_messages(chat_prompts_raw):
        '''
        LangChain 모델에 사용할 수 있도록 입력된 메시지 목록을 변환합니다.

        Args:
            chat_prompts_raw (List[Union[dict, BaseMessage]]): 
                'role'과 'content'를 포함한 딕셔너리 형태 또는 
                LangChain의 메시지 객체(BaseMessage 하위 클래스)로 구성된 리스트.

        Returns:
            List[BaseMessage]: 
                SystemMessage, HumanMessage, AIMessage 등 LangChain에서 사용하는 메시지 객체 리스트.

        Raises:
            ValueError: 
                알 수 없는 역할(role)이 있는 경우 또는 지원하지 않는 타입이 포함된 경우 예외를 발생시킵니다.
        '''
        converted = []
        for item in chat_prompts_raw:
            if isinstance(item, dict):
                role = item.get("role")
                content = item.get("content", "")
                if role == "system":
                    converted.append(SystemMessage(content=content))
                elif role == "user":
                    converted.append(HumanMessage(content=content))
                elif role == "assistant":
                    converted.append(AIMessage(content=content))
                else:
                    raise ValueError(f"Unknown role: {role}")
            elif isinstance(item, BaseMessage):
                converted.append(item)
            else:
                raise ValueError(f"Unsupported chat_prompt type: {type(item)}")
        return converted

    # Define the node that calls the model
    async def call_model_node(self,
        state: CodeChatState,
        config: RunnableConfig,
        writer: StreamWriter
    ):
        chat_history = self.format_chat_history(state=state)
        user_query = self.get_last_user_message(state=state)
        
        # chat_type:str # 01: 검색어 찾기, 02: 질문하기, 03: 후속질문하기, 04: 제목짓기, 05: 태그 추출
        chat_type = state.get('chat_type', '02')

        chat_prompts = []
        
        if (chat_type == "01") :
            chat_prompts = self.langfuse.get_prompt("AXLR_UI_CHAT_CODE_01").compile(
                current_date = datetime.now().strftime("%Y-%m-%d"), # 현재일자를 yyyy-mm-dd 형식으로 포맷
                chat_history = chat_history
            )
        elif (chat_type == "02") :
            chat_prompts = self.langfuse.get_prompt("AXLR_UI_CHAT_CODE_02").compile(
                context = state.get("context", ""),
                user_query = user_query
            )
        elif (chat_type == "03") :
            chat_prompts = self.langfuse.get_prompt("AXLR_UI_CHAT_CODE_03").compile(
                chat_history = chat_history
            )
        elif (chat_type == "04") :
            chat_prompts = self.langfuse.get_prompt("AXLR_UI_CHAT_CODE_04").compile(
                chat_history = chat_history
            )
        elif (chat_type == "05") :
            chat_prompts = self.langfuse.get_prompt("AXLR_UI_CHAT_CODE_05").compile(
                chat_history = chat_history
            )
            
        # system 메세지 뒤에 채팅이력 추가
        messages = (state.get("messages") or [])[:-1]
        # @todo messages 길이를 체크해서 filter 로직 추가

        if chat_type in ("02") and isinstance(chat_prompts, list):
            last_system_idx = -1
            for idx, msg in enumerate(chat_prompts):
                if isinstance(msg, dict) and msg.get("role") == "system":
                    last_system_idx = idx
            if last_system_idx >= 0:
                if messages:
                    chat_prompts = chat_prompts[:last_system_idx+1] + messages + chat_prompts[last_system_idx+1:]

        # LangChain 모델에 사용할 수 있도록 입력된 메시지 목록을 변환
        chat_prompts = self.convert_to_messages(chat_prompts)
            

        # Stream 방식
        tokens = []
        async for chunk in self.model.astream(chat_prompts, config):
            writer(chunk)
            tokens.append(str(chunk.content))
        state['response'] = "".join(tokens)

        # result = await self.model.ainvoke(chat_prompts)  # 동기 호출로 변경
        # state["response"] = result.content
        
        return state

    # Define the conditional edge that determines whether to continue or not
    def should_continue(self, state: CodeChatState):
        messages = state["messages"]
        last_message = messages[-1]
        # If there is no function call, then we finish
        if not last_message.tool_calls:
            return "end"
        # Otherwise if there is, we continue
        else:
            return "continue"


    def clean_response_node(self, state: CodeChatState) -> CodeChatState:
        # chat_type이 02인 경우만 아래 로직을 타도록
        if state.get("chat_type") == "02":
            # Remove <source ...>태그와 그 뒤에 붙은 '는', '은', '이', '가' 조사까지 함께 제거
            cleaned = re.sub(r"<source[^>]*>[ \t]*(?:는|은|이|가)?", "", state["response"])
            cleaned = re.sub(r"</source>", "", cleaned)
            state["response"] = cleaned
        return state


    # 1. file 컨텍스트가 없을 경우
    # 2. LLM 

    async def search_vector_datas_node(self, state:CodeChatState) -> CodeChatState:

        index_name = "code_assist" # 추후 입력값을 받을 수 있도록 변경
        search_text = self.get_last_user_message(state)

        # 체크
        if not search_text:
            return state

        vector_store = get_vector_store(collection_name=index_name)
        search_results = vector_store.similarity_search_with_score(query=search_text, k=5)
        
        context_datas = state.get("context_datas", [])

        for i, vector_data in enumerate(search_results, start=1):
            context_datas.append({
                "id": vector_data["id"],
                "seq": -1,
                "type": "vectordb",
                "name": f"vectordb_{i}", # 이부분 수정필요. 조회된 vector 조각이 어디서 왔는지 확인이 필요함
                "content": vector_data.get("content", "")
            })
        state["context_datas"] = context_datas

        # webui에 인용정보를 보여주기 위하여 저장한다
        if search_results:
            self._store_vector_sources(state, search_results, context_datas)
        
        return state

    def _store_vector_sources(self, state: 'CodeChatState', search_results, context_datas):
        metadata = state.get("metadata")
        chat_type = metadata.get("chat_type") if metadata else None
        user_id = metadata.get("user_id") if metadata else None
        chat_id = metadata.get("chat_id") if metadata else None
        message_id = metadata.get("message_id") if metadata else None
        
        print(f"### [벡터 소스 저장] user_id: {user_id}, chat_id: {chat_id}, message_id: {message_id}, chat_type: {chat_type}")
        
        if user_id and chat_id and message_id:
            doc_id = search_results[0].get("doc_id", "")
            contents = [item.get("content", "") for item in context_datas if isinstance(item.get("content", ""), str)]
            source = make_source_item(user_id=user_id, resrc_org_id=doc_id, resrc_name=f"milvus_{doc_id}", context_datas=contents)

            with get_axlr_session() as session:
                # 조회
                chat_row = session.query(Chat).filter(Chat.id == chat_id).first()
                if chat_row and chat_row.chat:
                    try:
                        chat_data = chat_row.chat

                        # content가 문자열인지 확인하고, 인코딩 문제 예방을 위한 보정
                        if isinstance(chat_data, str):
                            chat_data = json.loads(chat_data)
                        if isinstance(chat_data, bytes):
                            chat_data = json.loads(chat_data.decode("utf-8", errors="replace"))
                        elif not isinstance(chat_data, dict):
                            chat_data = {}

                        # 메시지에 소스 추가
                        _history_messages = chat_data.get("history", {}).get("messages", {})
                        _history_msg = _history_messages.get(message_id)
                        
                        if _history_msg:
                            _history_msg.setdefault("sources", []).append(source)
                        
                        if message_id and isinstance(chat_data, dict):
                            # 메시지 목록 가져오기
                            _messages = chat_data.get("messages", [])
                            for msg in _messages:
                                if msg.get("id") == message_id:
                                    # sources에 소스 추가
                                    msg.setdefault("sources", [])
                                    msg["sources"].append(source)
                                    
                                    # 파일목록에 소스 추가
                                    chat_data.setdefault("files", []).append(source.get("source"))

                                    # 업데이트된 chat_data 내용을 DB update
                                    chat_row.chat = chat_data
                                    flag_modified(chat_row, "chat")  # 변경 감지 강제
                                    session.flush()
                                    session.commit()
                                    break
                                
                        return chat_data
                    except Exception as e:
                        # 로깅을 추가하고 None 반환
                        print(f"Error parsing file data: {e}")
                        return None

    def check_need_vector_search_node(self, state: CodeChatState) -> CodeChatState:
        query = self.get_last_user_message(state)
        prompt = f"다음 질문에 대해 벡터DB에서 문서를 검색해야 하는지 판단해줘. 필요하면 'yes', 아니면 'no'만 답해줘:\n\n{query}"
        # result = await self.model.ainvoke([HumanMessage(content=prompt)])
        result = self.model.invoke([HumanMessage(content=prompt)])
        answer = result.content.strip().lower()
        
        decision = "yes" if "yes" in answer else "no"
        state["is_vector_search"] = decision
            
        return state

    def route_based_on_vector_need(self, state: CodeChatState) -> str:
        return state.get("is_vector_search", "no")


    def get_chain(self, thread_id: str = str(uuid.uuid4()), checkpointer = None):
        # tools = [self.get_weather]
        # self.model = self.model.bind_tools(tools)
        
        graph = StateGraph(CodeChatState)
        
        graph.add_node("pre_process", self.pre_process_node)
        graph.add_node("check_need_vector_search", self.check_need_vector_search_node)
        graph.add_node("merge_context_datas", self.merge_context_datas_node)
        graph.add_node("search_vector_datas", self.search_vector_datas_node)
        graph.add_node("call_model", self.call_model_node)
        graph.add_node("clean_response", self.clean_response_node)

        graph.set_entry_point("pre_process")
        graph.add_edge("pre_process", "check_need_vector_search")
        graph.add_conditional_edges(
            "check_need_vector_search",
            self.route_based_on_vector_need,
            {
                "yes": "search_vector_datas",
                "no": "merge_context_datas"
            }
        )
        graph.add_edge("search_vector_datas", "merge_context_datas")
        graph.add_edge("merge_context_datas", "call_model")
        graph.add_edge("call_model", "clean_response")
        graph.add_edge("clean_response", END)
        # graph.add_edge("tools", "call_model")

        return graph.compile(checkpointer=checkpointer), thread_id


def make_source_item(user_id:str, resrc_org_id:str, resrc_name:str, context_datas:list) -> dict:
    created_at = int(time.time())

    source = {
        "source": {
            "type": "milvus",
            "file": {
                "id": resrc_org_id, # resrc_org_id
                "user_id": user_id, # 넘겨준 값 유지
                "hash": "", # 생성
                "filename": resrc_name, # resrc_name
                "data":{
                    "content": "\n".join(context_datas)
                },
                "meta": {
                    "name": resrc_name, # resrc_name
                    "content_type": "text/plain", # 같은 값
                    "size": 0, # size
                    "data": {},
                    "collection_name": "" # 빈값
                },
                "created_at": created_at, # 생성
                "updated_at": created_at  # 생성
            },
            "id": resrc_org_id, # resrc_org_id
            "url": f"/api/v1/files/{resrc_org_id}", # 뒤에 resrc_org_id 붙이기
            "name": resrc_name, # resrc_name
            "collection_name": "", # 빈겂
            "status": "retrieve", # retrieve
            "size": 0, # text length
            "error": "", # 빈값
            "itemId": "" # 빈값
        },
        "document": context_datas,
        "metadata": [
            {
                "created_by": user_id, # 넘겨준 값 유지 (user_id)
                "embedding_config": {"engine": "", "model": "sentence-transformers/all-MiniLM-L6-v2"}, # bge-m3
                "file_id": resrc_org_id, # 빈겂
                "hash": "", # 빈겂
                "name": resrc_name,
                "source": resrc_name,
                "start_index":0 # 0
            }
            for _ in context_datas
        ],
        "distances": [1.0 for _ in context_datas]
        # [ 가능하면 score 값을 넘겨주도록 추후 수정
        #     0.7450273014932309,
        #     0.7285945578988293
        # ]
    }
    
    return source

if __name__ == "__main__":
    """
    Langfuse 프롬프트를 가져와 현재일자와 chat_history를 사용해 prompt를 컴파일합니다.
    """
    test = Langfuse().get_prompt("AXLR_UI_CHAT_CODE_01").compile(
        current_date=datetime.now().strftime("%Y-%m-%d"),
        chat_history="chat_history"
    )
    
    print(test)

    # from langchain_core.messages import HumanMessage
    
    # graph = await CodeChatAgent.create(index_name="cg_code_assist")

    # config = {"configurable": {"thread_id": "2"}}
    # input_message = HumanMessage(content="안녕! 내 이름은 홍길동이야")
    # for event in graph.stream({"messages": [input_message]}, config, stream_mode="values"):
    #     event["messages"][-1].pretty_print()


    # input_message = HumanMessage(content="내 이름이 뭐야?")
    # for event in graph.stream({"messages": [input_message]}, config, stream_mode="values"):
    #     event["messages"][-1].pretty_print()
