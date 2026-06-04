from fastapi import APIRouter

from src.schemas.chat_schema import ChatRequest
from src.services.diagnosis_service import diagnosis_service
from src.utils.response import success_response

router = APIRouter()

@router.post("/chat")
def chat(request: ChatRequest):
  result = diagnosis_service.process_message(request.message)
  return success_response(
    message="Respuesta generada correctamente",
    data=result
  )