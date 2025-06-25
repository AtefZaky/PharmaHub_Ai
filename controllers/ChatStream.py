import json
from config.models import llm

from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from helpers.chatHistory import get_or_create_history
from fastapi import Body
from typing import Optional, Dict,AsyncGenerator
from functions.ProcessDocFromUrl import process_file_from_url

# class QuestionRequest(BaseModel):
#     question: str = Field(..., min_length=1)
#     context: str | None = None
#     reqType: str = Field(..., pattern="^(doc|db)$")
#     table: list[dict] | str | None = None

class QuestionRequest(BaseModel):
    question: str = Field(..., min_length=1)
    user_id: int
    session_id: int
    user_info: Optional[Dict] = None
    type: Optional[int] = None
    url: Optional[str] = None

async def stream_response(question_request: QuestionRequest= Body(...)):
    print(question_request)

    user_id = question_request.user_id
    session_id = question_request.session_id
    user_question = question_request.question
    type = question_request.type

    if type is None:
        type = 0
    elif type is ['doc', 1]:
        type = 1

    chat_history = get_or_create_history(user_id, session_id)

    async def generate() -> AsyncGenerator[str, None]:
        chat_history.add_user_message(user_question)
        if type == 1 or type == 2:
            # Process the document from the URL
            if question_request.url:
                result = await process_file_from_url(question_request.url, type=type)
                if type == 2:
                    if isinstance(result, dict) and "matched_drugs" in result:
                        matched_drugs = result["matched_drugs"]
                        chat_history.add_ai_message(f"Matched Drugs: {matched_drugs}")
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
                    context = result["context"]
                    chat_history.add_user_message(context)
                else:
                    chat_history.add_ai_message("Unsupported file type or error processing the file.")
                    yield f"data: {json.dumps('Unsupported file type or error processing the file.')}\n\n"
            else:
                chat_history.add_ai_message("No URL provided for document processing.")
                yield f"data: {json.dumps('No URL provided for document processing.')}\n\n"

        response = llm.stream(chat_history.messages)

        if response is None:
            error_message = "No response from the model."
            chat_history.add_ai_message(error_message)
            yield f"data: {json.dumps(error_message)}\n\n"
            return
        
        try:
            full_answer = ""
            for chunk in response:
                content = chunk.content
                print(content) 
                full_answer = full_answer + content
                sse_chunk = f"data: {json.dumps(content)}\n\n"
                with open("output.txt", "a", encoding="utf-8") as f:
                   f.write(content)  # Append each chunk with a newline
                yield sse_chunk

            chat_history.add_ai_message(full_answer)
            yield "event: end\n"

        except Exception as e:

            error_message = f"Error: {str(e)}"
            yield f"event: error\n"
            yield f"data: {json.dumps(error_message)}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")
