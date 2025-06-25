from fastapi import APIRouter
from controllers.ChatStream import stream_response,ocr_prescription # Import functions
router = APIRouter()


router.post("/api/chat")(stream_response)
router.post("/api/prescription")(ocr_prescription)