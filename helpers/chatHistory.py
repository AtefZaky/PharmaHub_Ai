history = {}

from langchain_community.chat_message_histories import ChatMessageHistory

def get_or_create_history(user_id: int, session_id: str):
    """Retrieves or initializes a chat history for a given user and session."""
    if user_id not in history:
        history[user_id] = {}

    if session_id not in history[user_id]:
        history[user_id][session_id] = ChatMessageHistory()
        history[user_id][session_id].add_ai_message(
            "You are a professional medical assistant specialized in medications and interpreting medical test results. "
            "You always respond in English in a clear, accurate, and helpful way. "
            "When asked about a drug, provide details such as the active ingredient, indications, dosage, and possible side effects. "
            "When asked about a lab or analysis report, explain the results, include normal reference ranges, and highlight any abnormal values that require medical attention. "
            "You may also receive prescriptions (as text) and be asked to identify or extract drug names from them. In such cases, list the medications found and provide brief information about each."
        )

    return history[user_id][session_id]