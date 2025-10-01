# ===============================
# EcoBot - Dockerfile (API solo)
# ===============================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MPLBACKEND=Agg

# tini para manejo limpio de señales
RUN apt-get update && apt-get install -y --no-install-recommends tini \
    && rm -rf /var/lib/apt/lists/*

# Carpeta de trabajo
WORKDIR /app

# Dependencias
COPY requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Código
COPY app ./app

# Salidas (gráficos)
RUN mkdir -p /app/out

EXPOSE 8000

ENTRYPOINT ["/usr/bin/tini","--"]
CMD ["uvicorn","app.server_api:app","--host","0.0.0.0","--port","8000","--workers","2"]
