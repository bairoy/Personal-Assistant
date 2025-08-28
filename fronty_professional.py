import gradio as gr
from chat_handler import ChatHandler
from typing import List, Tuple
import os 
from langsmith import traceable

from dotenv import load_dotenv

load_dotenv()

os.environ['LANGSMITH_PROJECT']="Jarvish-bot"

# Initialize chat handler
chat_handler = ChatHandler()
DEFAULT_USER = "default_user"


def chat_function(message: str, history: List[List[str]]) -> Tuple[List[List[str]], str]:
    if not message.strip():
        return history, ""
    ai_reply = chat_handler.process_message(message, DEFAULT_USER)
    history.append([message, ai_reply])
    return history, ""


def load_session(session_choice: str) -> List[List[str]]:
    if not session_choice:
        return []
    session_id = session_choice[1] if isinstance(session_choice, tuple) else session_choice
    chat_handler.set_session(session_id)
    return chat_handler.get_session_history(session_id)


def refresh_sessions() -> gr.Dropdown:
    choices = chat_handler.get_user_sessions_formatted(DEFAULT_USER)
    return gr.Dropdown(choices=choices)


def new_session() -> Tuple[List[List[str]], gr.Dropdown]:
    chat_handler.create_new_session(DEFAULT_USER)
    choices = chat_handler.get_user_sessions_formatted(DEFAULT_USER)
    return [], gr.Dropdown(choices=choices)


def delete_session_handler(session_choice: str) -> Tuple[List[List[str]], gr.Dropdown]:
    if not session_choice:
        return [], gr.Dropdown(choices=[])
    session_id = session_choice[1] if isinstance(session_choice, tuple) else session_choice
    chat_handler.delete_session(session_id)
    choices = chat_handler.get_user_sessions_formatted(DEFAULT_USER)
    return [], gr.Dropdown(choices=choices)

# ----------------- Professional Interface -----------------

def create_interface():
    with gr.Blocks(title="🤖 AI Chatbot", theme=gr.themes.Soft()) as demo:
        # Header
        gr.Markdown("## 🤖 AI Chatbot with Session Management")
        gr.Markdown("Manage multiple sessions and chat seamlessly with the AI.")
        
        with gr.Row():
            # ---------------- Left Panel: Sessions ----------------
            with gr.Column(scale=1):
                gr.Markdown("### Session Management")
                sessions_dropdown = gr.Dropdown(
                    label="Select a Session",
                    choices=[],
                    interactive=True,
                    type="value"
                )
                with gr.Row():
                    refresh_btn = gr.Button("🔄 Refresh", size="sm", variant="secondary")
                    new_session_btn = gr.Button("➕ New Session", size="sm", variant="primary")
                    delete_btn = gr.Button("🗑️ Delete", size="sm", variant="stop")
            
            # ---------------- Right Panel: Chat ----------------
            with gr.Column(scale=3):
                chatbot_interface = gr.Chatbot(
                    label="Chat",
                    height=550,
                    show_copy_button=True,
                    elem_id="chatbox"
                )
                with gr.Row():
                    message_input = gr.Textbox(
                        label="Type your message here...",
                        placeholder="Enter message...",
                        lines=1,
                        scale=4
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)
        
        # ---------------- Event Handlers ----------------
        send_btn.click(
            chat_function,
            inputs=[message_input, chatbot_interface],
            outputs=[chatbot_interface, message_input]
        )
        message_input.submit(
            chat_function,
            inputs=[message_input, chatbot_interface],
            outputs=[chatbot_interface, message_input]
        )
        refresh_btn.click(
            refresh_sessions,
            outputs=[sessions_dropdown]
        )
        new_session_btn.click(
            new_session,
            outputs=[chatbot_interface, sessions_dropdown]
        )
        sessions_dropdown.change(
            load_session,
            inputs=[sessions_dropdown],
            outputs=[chatbot_interface]
        )
        delete_btn.click(
            delete_session_handler,
            inputs=[sessions_dropdown],
            outputs=[chatbot_interface, sessions_dropdown]
        )
    return demo

if __name__ == "__main__":
    demo = create_interface()
    demo.launch(server_name="0.0.0.0", server_port=7860)
