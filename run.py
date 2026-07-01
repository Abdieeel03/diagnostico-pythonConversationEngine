import os
import uvicorn

from src.config.settings import settings


if __name__ == "__main__":
  reload = os.getenv("RELOAD", "").lower() in ("true", "1", "yes")
  uvicorn.run(
    "src.main:app",
    host="0.0.0.0",
    port=settings.port,
    reload=reload
  )