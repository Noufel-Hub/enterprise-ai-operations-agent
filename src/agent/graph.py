from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, MessagesState, START
from langgraph.prebuilt import ToolNode, tools_condition

from src.tools.sensor_tools import get_latest_measurement


load_dotenv()

tools = [get_latest_measurement]

llm = ChatGoogleGenerativeAI(
    model="gemini-3.5-flash-lite",
    max_retries=1
)

llm_with_tools = llm.bind_tools(tools)


def call_model(state: MessagesState):
    response = llm_with_tools.invoke(state["messages"])
    return {"messages": [response]}


def build_agent():
    graph_builder = StateGraph(MessagesState)

    graph_builder.add_node("agent", call_model)
    graph_builder.add_node("tools", ToolNode(tools))

    graph_builder.add_edge(START, "agent")
    graph_builder.add_conditional_edges("agent", tools_condition)
    graph_builder.add_edge("tools", "agent")

    return graph_builder.compile()


agent = build_agent()