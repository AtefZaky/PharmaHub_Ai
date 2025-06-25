history = {}

from langchain_community.chat_message_histories import ChatMessageHistory

def get_or_create_history(user_id: int, session_id: str):
    """Retrieves or initializes a chat history for a given user and session."""
    if user_id not in history:
        history[user_id] = {}

    if session_id not in history[user_id]:
        history[user_id][session_id] = ChatMessageHistory()
        history[user_id][session_id].add_ai_message("You are a helpful Arabic assistant that answers user questions in Arabic.")

    return history[user_id][session_id]