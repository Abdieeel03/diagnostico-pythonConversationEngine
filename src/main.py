from fastapi import FastAPI

from src.utils.response import success_response
from src.routes.health_routes import router as health_router
from src.routes.chat_routes import router as chat_router

app = FastAPI(
  title="Python Conversation Engine",
  description="Un motor de conversación en Python para manejar interacciones de chat y procesamiento de lenguaje natural.",
  version="0.1.0"
)

app.include_router(health_router)
app.include_router(chat_router)

@app.get("/")
def root():
  return success_response(
    "Python Conversation Engine funcionando correctamente!",
    {
      "service": "Python Conversation Engine",
      "version": "0.1.0",
      "status": "ok"
    }
  )