import json
from config.models import get_agent

from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from helpers.chatHistory import get_or_create_history
from fastapi import Body
from typing import Optional, Dict,AsyncGenerator
from functions.ProcessDocFromUrl import process_file_from_url
from langchain.schema import messages_from_dict
from langchain.schema import AIMessage, HumanMessage


# class QuestionRequest(BaseModel):
#     question: str = Field(..., min_length=1)
#     context: str | None = None
#     reqType: str = Field(..., pattern="^(doc|db)$")
#     table: list[dict] | str | None = None

llm = get_agent()

def format_history_as_prompt(history):
    prompt_lines = []
    for msg in history:
        role = "User" if msg.type == "human" else "Assistant"
        prompt_lines.append(f"{role}: {msg.content}")
    return "\n".join(prompt_lines)

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1)
    user_id: str
    session_id: str
    user_info: Optional[Dict] = None
    type: Optional[int] = None
    url: Optional[str] = None


def stream_response(question_request: QuestionRequest= Body(...)):
    print(question_request)

    user_id = question_request.user_id
    session_id = question_request.session_id
    user_question = question_request.question
    type = question_request.type

    if type in [None, 0]:
        type = 0
    elif type in ['doc', 1]:
        type = 1
    elif type in ['image', 2]:
        type = 2

    chat_history = get_or_create_history(user_id, session_id)

    async def generate():
        # Example: prevent duplicate consecutive inputs
        if len(chat_history.messages) > 3 and hasattr(chat_history.messages[-2], 'content'):
            if chat_history.messages[-2].content.strip() == user_question.strip():
                chat_history.add_ai_message(chat_history.messages[-1])
                yield f"data: {json.dumps(chat_history.messages[-1].content)}\n\n"
                return
        chat_history.add_user_message(user_question)
        if type == 1 or type == 2:
            # Process the document from the URL
            if question_request.url:
                result = await process_file_from_url(question_request.url, type=type)
                if type == 2:
                    if isinstance(result, dict) and "Matched_Drugs" in result:
                        matched_drugs = result["Matched_Drugs"]
                        chat_history.add_ai_message(f"Matched Drugs From the Prescription the User Provide as Image: {matched_drugs}")
                        yield f"data: {json.dumps(matched_drugs)}\n\n"
                        return
                    else:
                        chat_history.add_ai_message("Error processing prescription or no drugs matched.")
                        yield f"data: {json.dumps('Error processing prescription or no drugs matched.')}\n\n"
                if isinstance(result, str):
                    chat_history.add_ai_message(result)
                    yield f"data: {json.dumps(result)}\n\n"
                    return
                elif isinstance(result, dict) and "context" in result:
                    print(result)
                    print(result["context"])
                    context = result["context"]
                    chat_history.add_user_message(context)
                else:
                    chat_history.add_ai_message("Unsupported file type or error processing the file.")
                    yield f"data: {json.dumps('Unsupported file type or error processing the file.')}\n\n"
            else:
                chat_history.add_ai_message("No URL provided for document processing.")
                yield f"data: {json.dumps('No URL provided for document processing.')}\n\n"
                
     
        all_messages = chat_history.messages
        if len(all_messages) > 6:
            all_messages = all_messages[-6:]
    
    # 1. Convert all messages to a safe format
        def convert_message(msg):
            if hasattr(msg, 'content'):  # Standard LangChain message
                return {
                    "role": "assistant" if isinstance(msg, AIMessage) else "user",
                    "content": msg.content
                }
            elif isinstance(msg, dict):  # Dictionary format
                return {
                    "role": msg.get("role", "user"),
                    "content": msg.get("content", str(msg))
                }
            elif type(msg).__name__ == 'AddableUpdatesDict':  # Special case
                return {
                    "role": "assistant" if msg.get('type') == 'ai' else "user",
                    "content": msg.get('content', str(msg))
                }
            else:  # Fallback for unknown types
                return {
                    "role": "user",
                    "content": str(msg)
                }
        
        # 2. Build the prompt with converted messages
        prompt = {
            "messages":[convert_message(msg) for msg in all_messages],
            "user_info": question_request.user_info or {}
        }
        
        # Debug: Print the final prompt structure
        print("Final Prompt Structure:", json.dumps(prompt, indent=2))
        
        try:
            response = llm.stream(prompt)
            print("Response from model:", response)
        
            if response is None:
                error_message = "No response from the model."
                chat_history.add_ai_message(error_message)
                yield f"data: {json.dumps(str(error_message))}\n\n"
                return
            full_answer = ""
            for chunk in response:
                print(chunk['agent']['messages'][0].content)
                content = chunk['agent']['messages'][0].content
                print(content) 
                full_answer = full_answer + content
                if hasattr(content, "content"):
                    yield f"data: {json.dumps(content.content)}\n\n"
                else:
                    yield f"data: {json.dumps(str(content))}\n\n"
                # sse_chunk = f"data: {json.dumps(str(content))}\n\n"
                with open("output.txt", "a", encoding="utf-8") as f:
                   f.write(content)  # Append each chunk with a newline
                # yield f"event: message\n"
                # yield sse_chunk
            if chat_history.messages[-1] == full_answer:
                return
            chat_history.add_ai_message(full_answer)
            yield "event: end\n"

        except Exception as e:

            error_message = f"Error: {str(e)}"
            yield f"event: error\n"
            yield f"data: {json.dumps(str(error_message))}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream", headers={
    "Cache-Control": "no-cache",
    "X-Accel-Buffering": "no",
})


class PerscriptionReq(BaseModel):
    type: Optional[int] = 2
    url: Optional[str] = None


async def ocr_prescription(question_request: PerscriptionReq = Body(...)):
    """
    Process the OCR prescription file and return matched drugs.
    
    Args:
        question_request (PrescriptionReq): Contains URL and type.

    Returns:
        dict: A dictionary containing matched drugs.
    """
    try:
        result = await process_file_from_url(question_request.url, 2)

        if isinstance(result, dict) and "Matched_Drugs" in result:
            matched_drugs = result["Matched_Drugs"]
            print(f"Matched Drugs: {matched_drugs}")
            return {"Matched_Drugs": matched_drugs}
        else:
            return {"Matched_Drugs": []}

    except Exception as e:
        print(f"Error processing OCR prescription: {str(e)}")
        return {"error": str(e)}