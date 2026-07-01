from fastapi import APIRouter

from src.schemas.chat_schema import ChatRequest
from src.services.diagnosis_service import diagnosis_service
from src.utils.response import success_response

router = APIRouter()

@router.post("/chat")
async def chat(request: ChatRequest):
  result = await diagnosis_service.process_message(
    message=request.message,
    session_id=request.session_id
  )
  return success_response(
    message="Respuesta generada correctamente",
    data=result
  )