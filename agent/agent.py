import os
from typing import Annotated, TypedDict, List, Any
from langgraph.graph import StateGraph, END, START
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from dotenv import load_dotenv

from agent.prompts.prompts import AGENT_PROMPT

load_dotenv()
from langchain_core.messages import (
    BaseMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)

from tools.tools import (
    delete_file,
    execute_file,
    create_file,
    read_file,
    edit_file,
    extract_table_from_url,
)

os.environ["GOOGLE_API_KEY"] = os.getenv("GOOGLE_API_KEY")

api_key = os.getenv("GOOGLE_API_KEY")

if "GOOGLE_API_KEY" not in os.environ:
    raise Exception(
        "GOOGLE_API_KEY is not set. Please set it as an environment variable."
    )

gemini_model = "gemini-2.0-flash"


llm = ChatGoogleGenerativeAI(
    model=gemini_model,
)

# Data Analyst Agent State


class AgentState(TypedDict):
    """
    Defines the state of the agent, which is passed between nodes in the graph.
    """

    messages: Annotated[List[BaseMessage | HumanMessage], add_messages]
    final_response: str | list[str | dict[Any, Any]] | None


# tools

tools = [
    execute_file,
    create_file,
    read_file,
    edit_file,
    extract_table_from_url,
    delete_file,
]

llm_with_tools = llm.bind_tools(tools)

# res = llm_with_tools.invoke("What is AI?")
#
# print(res.content)


def call_llm(state: AgentState) -> AgentState:
    system_message_content = AGENT_PROMPT
    llm_input_messages = [SystemMessage(content=system_message_content)] + state[
        "messages"
    ]

    print("\n\nLLM INPUT MESSAGES:", llm_input_messages[-1], "\n\n")

    response = llm_with_tools.invoke(llm_input_messages)

    state["messages"].append(response)

    return state


def should_continue(state: AgentState) -> str:
    """
    Determines the next step based on the LLM's output.
    If the LLM wants to call a tool, route to 'tools'. Otherwise, format the response.
    """
    print("---CONDITIONAL EDGE: SHOULD CONTINUE---")
    last_message = state["messages"][-1]
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        print("\n\nRouting to tools: ", last_message.tool_calls, "\n\n")
        return "tools"
    return "format_final_response"


def format_final_response(state: AgentState) -> AgentState:
    """
    Node to extract and format the final response from the LLM's output.
    This is the message that will be sent back to the user.
    """
    print("---NODE: FORMAT FINAL RESPONSE---")
    state["final_response"] = state["messages"][-1].content
    return state


tool_node = ToolNode(tools=tools)


def get_unified_agent_graph():
    """
    Builds and returns the LangGraph agent for the unified conversational flow.
    """
    workflow = StateGraph(AgentState)

    workflow.add_node("call_llm", call_llm)
    workflow.add_node("tools", tool_node)  # Use the ToolNode directly
    workflow.add_node("format_final_response", format_final_response)

    # Define the entry point
    workflow.add_edge(START, "call_llm")  # Use the START constant("call_llm")

    # Conditional edge from LLM call:
    # If the LLM decides to call a tool, go to 'tools'.
    # Otherwise (if it has a direct response), go to 'format_final_response'.
    workflow.add_conditional_edges(
        "call_llm",
        should_continue,
        {"tools": "tools", "format_final_response": "format_final_response"},
    )

    # After tools are executed, loop back to the LLM to process the tool's output
    workflow.add_edge("tools", "call_llm")

    # After formatting the final response, the graph ends
    workflow.add_edge("format_final_response", END)

    print("---BUILDING AGENT GRAPH---")
    graph = workflow.compile()
    with open("graph1.png", "wb") as f:
        f.write(graph.get_graph().draw_mermaid_png())

    return graph


def run_agent(qFilename: str):

    QUESTION = ""

    with open(qFilename, "r") as f:
        QUESTION = f.read()

    state = {"messages": [HumanMessage(content=QUESTION)], "final_response": ""}

    print("---RUNNING AGENT---")
    print("\n\nQUESTION:", QUESTION, "\n\n")

    graph = get_unified_agent_graph()
    resp = graph.invoke(state, {"recursion_limit": 100})

    return resp["final_response"]
