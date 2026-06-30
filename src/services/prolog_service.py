import httpx
from typing import Any

from src.config.settings import settings

class PrologService:
  def __init__(self):
    self.base_url = settings.prolog_engine_url
    self.timeout = httpx.Timeout(15.0, connect=5.0)
  
  async def get_health(self) -> dict[str, Any]:
    try:
      async with httpx.AsyncClient(timeout=self.timeout) as client:
        response = await client.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
      return e.response.json() if e.response else {
        "success": False,
        "message": f"Prolog respondio con error: {e.response.status_code if e.response else 'unknown'}",
        "data": None
      }

    except httpx.RequestError as e:
      return {
        "success": False,
        "message": f"Error en la conexion con Prolog: {str(e)}",
        "data": None
      }
  
  async def get_diagnostico(self, sintomas: list[str]) -> dict[str, Any]:
    try:
      async with httpx.AsyncClient(timeout=self.timeout) as client:
        response = await client.post(
          f"{self.base_url}/diagnostico",
          json={"sintomas": sintomas}
        )
        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as e:
      return e.response.json() if e.response else {
        "success": False,
        "message": f"Prolog respondio con error: {e.response.status_code if e.response else 'unknown'}",
        "data": None
      }

    except httpx.RequestError as e:
      return {
        "success": False,
        "message": f"Error en la conexion con Prolog: {str(e)}",
        "data": None
      }

prolog_service = PrologService()