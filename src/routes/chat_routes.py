from fastapi import APIRouter

from src.schemas.chat_schema import ChatRequest
from src.services.diagnosis_service import diagnosis_service
from src.utils.response import error_response, success_response

router = APIRouter()


@router.post('/chat')
async def chat(request: ChatRequest):
  try:
    result = await diagnosis_service.process_message(
      message=request.message,
      client_id=request.client_id,
      client_msg_id=request.client_msg_id,
    )
  except Exception as exc:
    return error_response(
      message=f'Error procesando el mensaje: {exc}',
      status_code=500,
    )

  return success_response(
    message='Respuesta generada correctamente',
    data=result,
  )
