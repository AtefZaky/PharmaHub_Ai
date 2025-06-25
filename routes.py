from fastapi import APIRouter
from controllers.ChatStream import stream_response # Import functions
router = APIRouter()

router.post("/api/chat")(stream_response)