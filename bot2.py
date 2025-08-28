from langgraph.graph import StateGraph,START,END 
from typing import TypedDict,Annotated 
from langchain_core.messages import BaseMessage ,HumanMessage
from langchain_openai import ChatOpenAI 
from langgraph.graph.message import add_messages 
from dotenv import load_dotenv 

from langgraph.checkpoint.postgres import PostgresSaver
from psycopg import Connection 
import os 
from langgraph.prebuilt import ToolNode, tools_condition 
import webbrowser 
from langchain_core.tools import tool 
import numpy as np
from setvectordb import playlists,index,model
import time 
from googleapiclient.discovery import build 

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

####------------Youtube-- Setup----####
youtube = build("youtube","v3",developerKey=os.getenv("YOUTUBE_API_KEY"))
## -----------------------------------

### --------Graph initialization-------
class ChatState(TypedDict):
  messages :Annotated[list[BaseMessage],add_messages]

##--------------------------------

### helper functions -----------
def get_playlist_id(query:str,k:int=1):
  query_embedding = model.encode([query],normalize_embeddings=True)
  distances,indices = index.search(np.array(query_embedding),k)
  best_idx = indices[0][0]
  return playlists[best_idx]["id"]
## ---------------------------------


####----------Custom tools ----------
@tool
def open_url(link:str):
  """a simple url opener tool that opens the url in the browser"""
  webbrowser.open(link)

@tool
def youtube_search(query:str):
  """Search YouTube for a video or song by query. 
    Use this when the user asks to play a specific song, video, or when the request 
    doesn’t clearly mention a playlist."""
  url = f"https://www.youtube.com/results?search_query={query}"
  webbrowser.open(url)
  return f"{query} opened on youtube on chrome browser"

@tool
def play_playlist(query:str)->str:
  """Play a YouTube playlist by query or ID.
    Use this only when the user specifically mentions a playlist, 
    album, mix, or wants continuous playback."""
  playlist_id = get_playlist_id(query)
  if playlist_id:
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    webbrowser.open(url)
    return f"playing playlist for {query}"
  else:
    return f"No playlist found for {query}"


### ------ Tool set up -------------
tools = [open_url,youtube_search,play_playlist]
tool_node = ToolNode(tools)
##-----------------------------------

### -- llm with tool ------------
llm_with_tools = llm.bind_tools(tools)
## -----------------------

### --------- Node functions -------
def chat_node(state:ChatState):
  messages = state['messages']
  response = llm_with_tools.invoke(messages)
  return {"messages":[response]}
## --------------------------------

##----------- Graph set up -------------
graph = StateGraph(ChatState)
graph.add_node("chat_node",chat_node)
graph.add_node("tools",tool_node)

graph.add_edge(START,"chat_node")
graph.add_conditional_edges("chat_node",tools_condition)
graph.add_edge('tools','chat_node')
graph.add_edge("chat_node",END)
##-----------------------------------

## --  graph compilation ---------------
chatbot = graph.compile(checkpointer=checkpointer)
## -------------------------------