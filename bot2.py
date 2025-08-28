from langgraph.graph import StateGraph,START,END 
from typing import TypedDict,Annotated 
from langchain_core.messages import BaseMessage ,HumanMessage
from langchain_openai import ChatOpenAI 
from langgraph.graph.message import add_messages 
from dotenv import load_dotenv 
from langchain_core.messages import HumanMessage 
from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection 
import os 


load_dotenv()

llm = ChatOpenAI(model="gpt-5-mini-2025-08-07")

DATABASE_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"

connection_kwargs = {
    "autocommit": True,
    "prepare_threshold": 0,
}
conn = Connection.connect(DATABASE_URL, **connection_kwargs)
checkpointer = PostgresSaver(conn)
checkpointer.setup()

class ChatState(TypedDict):
  messages :Annotated[list[BaseMessage],add_messages]

def chat_node(state:ChatState):
  messages = state['messages']
  response = llm.invoke(messages)
  return {"messages":[response]}

graph = StateGraph(ChatState)
graph.add_node("chat_node",chat_node)
graph.add_edge(START,"chat_node")
graph.add_edge("chat_node",END)
chatbot = graph.compile(checkpointer=checkpointer)
