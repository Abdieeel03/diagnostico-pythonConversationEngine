from fastapi import FastAPI

from src.utils.response import success_response

app = FastAPI(
  title="Python Conversation Engine",
  description="Un motor de conversación en Python para manejar interacciones de chat y procesamiento de lenguaje natural.",
  version="0.1.0"
)

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