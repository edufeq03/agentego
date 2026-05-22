FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema necessárias para compilar pacotes como psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*

# Copia os requirements da pasta backend
COPY backend/requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código da pasta backend
COPY backend/ .

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
