import gradio as gr
from langchain_core.messages import HumanMessage
from bot2 import chatbot
import uuid 
from database import conn
from datetime import datetime

conn.autocommit = True

# Database functions
def insert_message(session_id, sender, message_text):
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO messages (message_id, session_id, sender, message_text, created_at) 
            VALUES (%s, %s, %s, %s, %s)
            """,
            (str(uuid.uuid4()), session_id, sender, message_text, datetime.now())
        )

def create_session(user_id):
    session_id = str(uuid.uuid4())
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO sessions (session_id, user_id, start_time)
            VALUES (%s, %s, %s)
            """,
            (session_id, user_id, datetime.now())
        )
    return session_id

def create_user(username):
    user_id = str(uuid.uuid4())
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO users(user_id, username, created_at)
            VALUES (%s, %s, %s)
            """,
            (user_id, username, datetime.now())
        )
    return user_id

def get_or_create_user(username):
    with conn.cursor() as cur:
        # Check if user exists
        cur.execute("SELECT user_id FROM users WHERE username = %s", (username,))
        result = cur.fetchone()
        if result:
            return result[0]
        else:
            return create_user(username)

def get_session_messages(session_id):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT sender, message_text FROM messages 
            WHERE session_id = %s 
            ORDER BY created_at ASC
            """, 
            (session_id,)
        )
        return cur.fetchall()

def get_user_sessions(user_id):
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT session_id, start_time, 
                   (SELECT COUNT(*) FROM messages WHERE session_id = s.session_id) as msg_count
            FROM sessions s 
            WHERE user_id = %s 
            ORDER BY start_time DESC 
            LIMIT 10
            """, 
            (user_id,)
        )
        return cur.fetchall()

# Global variables for session management
current_user_id = None
current_session_id = None

def chat_function(message, history, username):
    global current_user_id, current_session_id
    
    if not username.strip():
        return history, ""
    
    # Get or create user
    if current_user_id is None:
        current_user_id = get_or_create_user(username)
    
    # Create session if none exists
    if current_session_id is None:
        current_session_id = create_session(current_user_id)
    
    # Insert user message
    insert_message(current_session_id, "user", message)
    
    # Get AI response
    config = {"configurable": {"thread_id": current_session_id}}
    response = chatbot.invoke({'messages': [HumanMessage(content=message)]}, config=config)
    ai_reply = response['messages'][-1].content
    
    # Insert AI response
    insert_message(current_session_id, "ai", ai_reply)
    
    # Add to history
    history.append([message, ai_reply])
    
    return history, ""

def load_session(username, session_choice):
    global current_user_id, current_session_id
    
    if not username.strip() or not session_choice:
        return []
    
    # Parse session_id from choice
    session_id = session_choice.split(" - ")[0].replace("Session ", "")
    current_session_id = session_id
    
    # Load messages
    messages = get_session_messages(session_id)
    history = []
    for sender, text in messages:
        if sender == "user":
            history.append([text, None])
        elif sender == "ai":
            if history and history[-1][1] is None:
                history[-1][1] = text
            else:
                history.append([None, text])
    
    return history

def refresh_sessions(username):
    global current_user_id
    
    if not username.strip():
        return gr.Dropdown(choices=[])
    
    current_user_id = get_or_create_user(username)
    sessions = get_user_sessions(current_user_id)
    
    choices = []
    for session_id, start_time, msg_count in sessions:
        choice_text = f"Session {session_id[:8]} - {start_time.strftime('%Y-%m-%d %H:%M')} ({msg_count} messages)"
        choices.append((choice_text, session_id))
    
    return gr.Dropdown(choices=choices)

def new_session(username):
    global current_user_id, current_session_id
    
    if not username.strip():
        return [], gr.Dropdown(choices=[])
    
    current_user_id = get_or_create_user(username)
    current_session_id = create_session(current_user_id)
    
    # Refresh sessions dropdown
    sessions = get_user_sessions(current_user_id)
    choices = []
    for session_id, start_time, msg_count in sessions:
        choice_text = f"Session {session_id[:8]} - {start_time.strftime('%Y-%m-%d %H:%M')} ({msg_count} messages)"
        choices.append((choice_text, session_id))
    
    return [], gr.Dropdown(choices=choices)

# Create Gradio interface
with gr.Blocks(title="AI Chatbot", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🤖 AI Chatbot with Database Storage")
    
    with gr.Row():
        with gr.Column(scale=1):
            username_input = gr.Textbox(
                label="Username", 
                placeholder="Enter your username",
                value="user1"
            )
            
            sessions_dropdown = gr.Dropdown(
                label="Chat Sessions",
                choices=[],
                interactive=True
            )
            
            refresh_btn = gr.Button("Refresh Sessions")
            new_session_btn = gr.Button("New Session")
        
        with gr.Column(scale=3):
            chatbot_interface = gr.Chatbot(
                label="Chat",
                height=500
            )
            
            message_input = gr.Textbox(
                label="Message",
                placeholder="Type your message here...",
                lines=1
            )
            
            send_btn = gr.Button("Send", variant="primary")
    
    # Event handlers
    send_btn.click(
        chat_function,
        inputs=[message_input, chatbot_interface, username_input],
        outputs=[chatbot_interface, message_input]
    )
    
    message_input.submit(
        chat_function,
        inputs=[message_input, chatbot_interface, username_input],
        outputs=[chatbot_interface, message_input]
    )
    
    refresh_btn.click(
        refresh_sessions,
        inputs=[username_input],
        outputs=[sessions_dropdown]
    )
    
    new_session_btn.click(
        new_session,
        inputs=[username_input],
        outputs=[chatbot_interface, sessions_dropdown]
    )
    
    sessions_dropdown.change(
        load_session,
        inputs=[username_input, sessions_dropdown],
        outputs=[chatbot_interface]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)