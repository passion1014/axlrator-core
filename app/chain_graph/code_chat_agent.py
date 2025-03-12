from typing import Annotated, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import uuid

from langchain_core.tools import tool

from langgraph.graph import StateGraph, END

from app.utils import get_llm_model
from app.vectordb.bm25_search import ElasticsearchBM25
from langfuse.callback import CallbackHandler

import json
from langchain_core.messages import ToolMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.types import StreamWriter
from sqlalchemy.ext.asyncio import AsyncSession

class CodeChatState(TypedDict):
    """The state of the agent."""
    thread_id: str
    # add_messages is a reducer
    # See https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers
    messages: Annotated[Sequence[BaseMessage], add_messages]
    

class CodeChatAgent:
    def __init__(self, index_name:str="cg_code_assist"):
        self.index_name = index_name
        
    @classmethod
    async def create(cls, index_name: str, session: AsyncSession) -> 'CodeChatAgent':
        # __init__ 호출
        instance = cls(index_name)
        
        instance.db_session = session
        # instance.faissVectorDB = await get_vector_db(collection_name=index_name, session=session)
        instance.es_bm25 = ElasticsearchBM25(index_name=index_name)
        instance.model = get_llm_model().with_config(callbacks=[CallbackHandler()])
        
        return instance



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


    # Define the node that calls the model
    async def call_model(self,
        state: CodeChatState,
        config: RunnableConfig,
        writer: StreamWriter
    ):
        system_prompt = SystemMessage(
            "You are a helpful AI assistant, please respond to the users query to the best of your ability!"
        )

        # Stream 방식
        tokens = []
        async for chunk in self.model.astream([system_prompt] + state["messages"], config):
            writer(chunk)
            tokens.append(chunk)
        return {"messages": tokens}


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

    def get_chain(self, thread_id: str = str(uuid.uuid4()), checkpointer = None):
        tools = [self.get_weather]
        # self.model = self.model.bind_tools(tools)
        
        graph = StateGraph(CodeChatState)
        graph.add_node("agent", self.call_model)
        graph.add_node("tools", self.tool_node)

        graph.set_entry_point("agent")

        # We now add a conditional edge
        graph.add_conditional_edges(
            "agent",
            self.should_continue,
            {
                "continue": "tools",
                "end": END,
            },
        )
        graph.add_edge("tools", "agent")

        chain = graph.compile(checkpointer=checkpointer)
        return chain, thread_id


if __name__ == "__main__":
    pass
    # from langchain_core.messages import HumanMessage
    
    # graph = await CodeChatAgent.create(index_name="cg_code_assist")

    # config = {"configurable": {"thread_id": "2"}}
    # input_message = HumanMessage(content="안녕! 내 이름은 홍길동이야")
    # for event in graph.stream({"messages": [input_message]}, config, stream_mode="values"):
    #     event["messages"][-1].pretty_print()


    # input_message = HumanMessage(content="내 이름이 뭐야?")
    # for event in graph.stream({"messages": [input_message]}, config, stream_mode="values"):
    #     event["messages"][-1].pretty_print()
