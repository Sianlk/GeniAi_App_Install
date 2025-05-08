FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python3", "core/ai_orchestrator/ai_orchestrator.py"]
