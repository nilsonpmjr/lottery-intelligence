FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY api/requirements.txt /app/api/requirements.txt
RUN pip install --no-cache-dir -r /app/api/requirements.txt

COPY lottery_intelligence/ /app/lottery_intelligence/
COPY api/ /app/api/
COPY loterias.db /app/loterias.db

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
