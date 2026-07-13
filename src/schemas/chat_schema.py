from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
  message: str = Field(..., min_length=1)
  client_id: str = Field(..., min_length=1, description="session_id que mantiene el frontend en localStorage")
  client_msg_id: str | None = Field(
    default=None,
    description="ID del mensaje del usuario para idempotencia en reintentos",
  )
