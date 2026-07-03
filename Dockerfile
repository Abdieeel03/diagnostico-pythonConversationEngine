FROM python:3.12.9-slim

WORKDIR /app

COPY diagnostico-pythonConversationEngine/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY diagnostico-pythonConversationEngine/src/ ./src/
COPY diagnostico-pythonConversationEngine/scripts/ ./scripts/
COPY diagnostico-pythonConversationEngine/alembic/ ./alembic/
COPY diagnostico-pythonConversationEngine/alembic.ini ./alembic.ini
COPY diagnostico-pythonConversationEngine/run.py ./run.py

COPY diagnostico-prologEngine/src/knowledge/facts/sintomas.pl /app/diagnostico-prologEngine/src/knowledge/facts/sintomas.pl

ENV PROLOG_FACTS_PATH=/app/diagnostico-prologEngine/src/knowledge/facts/sintomas.pl

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["python", "run.py"]
