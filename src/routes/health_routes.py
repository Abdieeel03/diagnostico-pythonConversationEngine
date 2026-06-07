from fastapi import APIRouter

from src.services.prolog_service import prolog_service
from src.utils.response import success_response

router = APIRouter()

@router.get("/health-prolog")
def health_prolog():
  health_status = prolog_service.get_health()
  return health_status