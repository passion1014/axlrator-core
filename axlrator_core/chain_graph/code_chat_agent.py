from datetime import datetime
import json
import re
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
    is_vector_search: str # yes or no 벡터를 조회할지 말지 여부    
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
                        import json
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
        
        return state


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
