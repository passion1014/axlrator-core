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



class CodeChatState(TypedDict):
    """The state of the agent."""
    thread_id: str
    chat_type:str # 01: 검색어 찾기, 02: 질문하기, 03: 후속질문하기, 04: 제목짓기, 05: 태그 추출
    messages: Annotated[Sequence[BaseMessage], add_messages] # add_messages is a reducer
    file_contexts: Optional[List[dict]] = None
    files: Optional[List[dict]] = None
    context:str
    response:str
    

class CodeChatAgent:
    def __init__(self, index_name:str="cg_code_assist"):
        self.index_name = index_name
        self.langfuse = Langfuse()
        
    @classmethod
    async def create(cls, index_name: str, session: AsyncSession) -> 'CodeChatAgent':
        # __init__ 호출
        instance = cls(index_name)
        
        instance.db_session = session
        # instance.faissVectorDB = await get_vector_db(collection_name=index_name, session=session)
        # instance.es_bm25 = ElasticsearchBM25(index_name=index_name)
        
        callback_handler = CallbackHandler()
        instance.callback_handler = callback_handler
        # instance.model = get_llm_model()
        instance.model = get_llm_model().with_config(callbacks=[callback_handler])
        instance.callback_handler = callback_handler
        
        
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

    # Add a context node to inject file context as a system message
    def add_file_context_node(self, state: CodeChatState) -> CodeChatState:
        parts = []

        if isinstance(state.get("files"), list):
            for i, file in enumerate(state["files"]):
                file_data = self.get_file_context(file["id"])
                if file_data:
                    _content = file_data.get("content", "")
                    if _content.strip():
                        parts.append(
                            f"<source id=\"{i+1}\" name=\"{file['name']}\">\n{_content}\n</source>"
                        )

        if isinstance(state.get("file_contexts"), list):
            parts.extend([
                f"<source id=\"{i+len(parts)+1}\" name=\"context_{i+1}\">\n{ctx['context']}\n</source>"
                # f"<source id=\"\" name=\"context_{i+1}\">\n{ctx['context']}\n</source>"
                for i, ctx in enumerate(state["file_contexts"])
                if ctx.get("context")
            ])

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
            chat_prompts = self.langfuse.get_prompt("AXLR_UI_CHAT_CODE_02").compile(
                chat_history = chat_history
            )
        elif (chat_type == "04") :
            chat_prompts = self.langfuse.get_prompt("AXLR_UI_CHAT_CODE_02").compile(
                chat_history = chat_history
            )
        elif (chat_type == "05") :
            chat_prompts = self.langfuse.get_prompt("AXLR_UI_CHAT_CODE_02").compile(
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


    def remove_source_tags_node(self, state: CodeChatState) -> CodeChatState:
        # Remove <source ...>태그와 그 뒤에 붙은 '는', '은', '이', '가' 조사까지 함께 제거
        cleaned = re.sub(r"<source[^>]*>[ \t]*(?:는|은|이|가)?", "", state["response"])
        cleaned = re.sub(r"</source>", "", cleaned)
        state["response"] = cleaned
        return state

    def get_chain(self, thread_id: str = str(uuid.uuid4()), checkpointer = None):
        # tools = [self.get_weather]
        # self.model = self.model.bind_tools(tools)
        
        graph = StateGraph(CodeChatState)
        graph.add_node("add_file_context", self.add_file_context_node)
        # graph.add_node("tools", self.tool_node)
        graph.add_node("agent", self.call_model_node)
        graph.add_node("clean_response", self.remove_source_tags_node)

        graph.set_entry_point("add_file_context")
        graph.add_edge("add_file_context", "agent")
        graph.add_edge("agent", "clean_response")
        graph.add_edge("clean_response", END)
        # graph.add_edge("agent", END)

        # # We now add a conditional edge
        # graph.add_conditional_edges(
        #     "agent",
        #     self.should_continue,
        #     {
        #         "continue": "tools",
        #         "end": END,
        #     },
        # )
        # graph.add_edge("tools", "agent")

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
