import httpx

from src.config.settings import settings

class PrologService:
  def __init__(self):
    self.base_url = settings.prolog_engine_url
  
  def get_health(self):
    try:
      response = httpx.get(f"{self.base_url}/health", timeout=5.0)

      response.raise_for_status()

      return response.json()
    
    except httpx.HTTPStatusError as e:
      return e.response.json() if e.response else {"status": "error", "message": str(e)}
    
    except httpx.RequestError as e:
      return {
        "success": False,
        "message": f"Error en la conexion con Prolog: {str(e)}",
        "data": None
      }
  
  def get_diagnostico(self, sintomas: list[str]):
    try:
      response = httpx.post(f"{self.base_url}/diagnostico", json={"sintomas": sintomas}, timeout= 10.0)
      
      response.raise_for_status()
      
      return response.json()
    
    except httpx.HTTPStatusError as e:
      return e.response.json() if e.response else {"status": "error", "message": str(e)}
    
    except httpx.RequestError as e:
      return {"status": "error", "message": f"Error en la conexion: {str(e)}"}

prolog_service = PrologService()