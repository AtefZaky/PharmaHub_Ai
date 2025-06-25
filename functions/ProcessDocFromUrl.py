from fastapi.responses import StreamingResponse
from pydantic.v1 import BaseModel, Field
from fastapi import HTTPException
import requests
import shutil
import os
from helpers.fileProcess import process_file
from model.OcrPrescription import OcrPrescription

class QuestionRequestUrl(BaseModel):
    url: str

async def process_file_from_url(url: str, type: int = 1):
    print(url)
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")
    
    try:

        response = requests.get(url, stream=True, verify=False, timeout=10)
        print(response)
        if response.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to download the file from the URL")

        file_name = url.split("/")[-1].split("?")[0]  # Remove query parameters
        file_name = file_name.replace(":", "_").replace("/", "_")  # Replace invalid characters if needed

        os.makedirs("temp", exist_ok=True)
        file_path = f"temp/{file_name}"

        with open(file_path, "wb") as file:
            shutil.copyfileobj(response.raw, file)

        if type == 1:
            result = process_file(file_path)

        elif type == 2:
            matched_drugs = OcrPrescription(file_path)
            result = {"Matched_Drugs": matched_drugs["Matched_Drugs"]}
        return result
    except Exception as e:
        print(e)