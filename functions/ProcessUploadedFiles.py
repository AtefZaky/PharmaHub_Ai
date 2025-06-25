
from fastapi import File, UploadFile, Form
from helpers.fileProcess import process_file

async def ask_about_doc(file: UploadFile = File(...)):

    allowed_types = ["application/pdf", "image/png", "image/jpeg", "application/vnd.ms-excel",
                     "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
    if file.content_type not in allowed_types:
        return {"error": "Unsupported file type"}

    file_location = f"temp/{file.filename}"
    with open(file_location, "wb") as buffer:
        buffer.write(await file.read())

    result = process_file(file_location)

    print(result)

    return result