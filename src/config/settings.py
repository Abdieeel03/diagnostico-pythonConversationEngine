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
    self.groq_api_key = os.getenv('GROQ_API_KEY', '')

    self.database_url = os.getenv(
      'DATABASE_URL',
      'postgresql+asyncpg://diagnostico:diagnostico_secret@localhost:5432/diagnostico_db'
    )

    self.auto_migrate = os.getenv('AUTO_MIGRATE', 'true').lower() in ('true', '1', 'yes')

settings = Settings()
