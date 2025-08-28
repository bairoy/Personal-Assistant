# fronty.py
import gradio as gr
from chat_handler import ChatHandler
from typing import List, Tuple

# Initialize chat handler
chat_handler = ChatHandler()

# Always use one default user
DEFAULT_USER = "default_user"

# --- Chat function ---
def chat_function(message: str, history: List[List[str]]) -> Tuple[List[List[str]], str]:
    """Handle chat message and return updated history"""
    if not message.strip():
        return history, ""
    
    try:
        ai_reply = chat_handler.process_message(message, DEFAULT_USER)
        history.append([message, ai_reply])
        return history, ""
    except Exception as e:
        history.append([message, f"Error: {str(e)}"])
        return history, ""

# --- Load session history ---
def load_session(session_choice: str) -> List[List[str]]:
    """Load selected session history"""
    if not session_choice:
        return []
    
    session_id = session_choice[1] if isinstance(session_choice, tuple) else session_choice
    chat_handler.set_session(session_id)
    return chat_handler.get_session_history(session_id)

# --- Refresh sessions dropdown ---
def refresh_sessions() -> gr.Dropdown:
    """Refresh sessions dropdown"""
    choices = chat_handler.get_user_sessions_formatted(DEFAULT_USER)
    return gr.Dropdown(choices=choices)

# --- Create new session ---
def new_session() -> Tuple[List[List[str]], gr.Dropdown]:
    """Create new session"""
    chat_handler.create_new_session(DEFAULT_USER)
    choices = chat_handler.get_user_sessions_formatted(DEFAULT_USER)
    return [], gr.Dropdown(choices=choices)

# --- Delete session ---
def delete_session_handler(session_choice: str) -> Tuple[List[List[str]], gr.Dropdown]:
    """Delete selected session"""
    if not session_choice:
        return [], gr.Dropdown(choices=[])
    
    session_id = session_choice[1] if isinstance(session_choice, tuple) else session_choice
    chat_handler.delete_session(session_id)
    
    choices = chat_handler.get_user_sessions_formatted(DEFAULT_USER)
    return [], gr.Dropdown(choices=choices)

# --- Create Gradio interface ---
def create_interface():
    # Populate dropdown at launch
    initial_sessions = chat_handler.get_user_sessions_formatted(DEFAULT_USER)

    with gr.Blocks(title="AI Chatbot", theme=gr.themes.Soft()) as demo:
        gr.Markdown("# 🤖 AI Chatbot with Sessions")
        
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown("### Session Management")
                sessions_dropdown = gr.Dropdown(
                    label="Chat Sessions",
                    choices=initial_sessions,
                    interactive=True
                )
                
                with gr.Row():
                    refresh_btn = gr.Button("Refresh", size="sm")
                    new_session_btn = gr.Button("New Session", size="sm", variant="primary")
                    delete_btn = gr.Button("Delete", size="sm", variant="stop")
            
            with gr.Column(scale=3):
                chatbot_interface = gr.Chatbot(
                    label="Chat",
                    height=500,
                    show_copy_button=True
                )
                
                with gr.Row():
                    message_input = gr.Textbox(
                        label="Message",
                        placeholder="Type your message here...",
                        lines=1,
                        scale=4
                    )
                    send_btn = gr.Button("Send", variant="primary", scale=1)

        # --- Event handlers ---
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
