FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN adduser --disabled-password --gecos "" --uid 1000 appuser

# Raiz do armazenamento de arquivos. O diretorio e criado na imagem e entregue ao
# appuser para que o volume nomeado montado aqui nasca com o dono certo: o Docker
# inicializa um volume vazio a partir do diretorio da imagem, preservando o dono.
# Sem isto o volume viria de root e o processo, que roda como appuser, nao gravaria.
RUN mkdir -p /var/lib/tattoo-studio/objects \
    && chown -R appuser:appuser /var/lib/tattoo-studio

FROM base AS development

COPY backend/pyproject.toml ./
RUN pip install --upgrade pip && pip install -e ".[dev]"

COPY backend/ ./
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS production

COPY backend/pyproject.toml ./
RUN pip install --upgrade pip && pip install .

COPY backend/ ./
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
