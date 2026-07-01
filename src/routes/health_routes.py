from fastapi import APIRouter

from src.services.prolog_service import prolog_service
from src.utils.response import success_response, error_response

router = APIRouter()

@router.get("/health")
def health():
  return success_response(
    "Python Conversation Engine funcionando correctamente",
    {
      "service": "python-conversation-engine",
      "version": "0.1.0",
      "status": "ok"
    }
  )

@router.get("/health-prolog")
async def health_prolog():
  health_status = await prolog_service.get_health()
  if health_status.get("success"):
    return success_response(
      health_status.get("message", ""),
      health_status.get("data")
    )
  return error_response(
    health_status.get("message", "Prolog no disponible"),
    status_code=503
  )