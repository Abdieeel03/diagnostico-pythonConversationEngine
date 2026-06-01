import os

from dotenv import load_dotenv

load_dotenv()

class Settings:
  def __init__(self):
    self.prolog_engine_url = os.getenv(
      'PROLOG_ENGINE_URL',
      'http://localhost:5000'
    )
    self.port = int(os.getenv('PORT', '8000'))

settings = Settings()