from typing import Annotated, Literal, Sequence, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
import uuid

from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import MessagesState, StateGraph, START, END
from langgraph.prebuilt import ToolNode

from app.db_model.database import SessionLocal
from app.utils import get_llm_model
from app.vectordb.bm25_search import ElasticsearchBM25
from app.vectordb.faiss_vectordb import FaissVectorDB
from langfuse.callback import CallbackHandler

import json
from langchain_core.messages import ToolMessage, SystemMessage
from langchain_core.runnables import RunnableConfig


class CodeChatState(TypedDict):
    """The state of the agent."""
    thread_id: str
    # add_messages is a reducer
    # See https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers
    messages: Annotated[Sequence[BaseMessage], add_messages]
    

class CodeChatAgent:
    def __init__(self, index_name:str="cg_code_assist"):
        self.index_name = index_name
        self.db_session = SessionLocal()
        self.faissVectorDB = FaissVectorDB(db_session=self.db_session, index_name=index_name)
        self.es_bm25 = ElasticsearchBM25(index_name=index_name)
        self.model = get_llm_model().with_config(callbacks=[CallbackHandler()])


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
    def call_model(self,
        state: CodeChatState,
        config: RunnableConfig,
    ):
        # this is similar to customizing the create_react_agent with state_modifier, but is a lot more flexible
        system_prompt = SystemMessage(
            "You are a helpful AI assistant, please respond to the users query to the best of your ability!"
        )
        response = self.model.invoke([system_prompt] + state["messages"], config)
        # We return a list, because this will get added to the existing list
        return {"messages": [response]}


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
        self.model = self.model.bind_tools(tools)
        
        workflow = StateGraph(CodeChatState)
        workflow.add_node("agent", self.call_model)
        workflow.add_node("tools", self.tool_node)

        # Set the entrypoint as `agent`
        # This means that this node is the first one called
        workflow.set_entry_point("agent")

        # We now add a conditional edge
        workflow.add_conditional_edges(
            # First, we define the start node. We use `agent`.
            # This means these are the edges taken after the `agent` node is called.
            "agent",
            # Next, we pass in the function that will determine which node is called next.
            self.should_continue,
            # Finally we pass in a mapping.
            # The keys are strings, and the values are other nodes.
            # END is a special node marking that the graph should finish.
            # What will happen is we will call `should_continue`, and then the output of that
            # will be matched against the keys in this mapping.
            # Based on which one it matches, that node will then be called.
            {
                # If `tools`, then we call the tool node.
                "continue": "tools",
                # Otherwise we finish.
                "end": END,
            },
        )

        # We now add a normal edge from `tools` to `agent`.
        # This means that after `tools` is called, `agent` node is called next.
        workflow.add_edge("tools", "agent")

        graph = workflow.compile(checkpointer=checkpointer)
        return graph, thread_id


if __name__ == "__main__":
    from langchain_core.messages import HumanMessage
    
    graph = CodeChatAgent(index_name="cg_code_assist")

    config = {"configurable": {"thread_id": "2"}}
    input_message = HumanMessage(content="안녕! 내 이름은 홍길동이야")
    for event in graph.stream({"messages": [input_message]}, config, stream_mode="values"):
        event["messages"][-1].pretty_print()


    input_message = HumanMessage(content="내 이름이 뭐야?")
    for event in graph.stream({"messages": [input_message]}, config, stream_mode="values"):
        event["messages"][-1].pretty_print()
