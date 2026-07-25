FROM python:3.11-slim

WORKDIR /app

# Which dependency set to install:
#   requirements.txt       full — includes sentence-transformers, so local RAG
#                          embedding works. Pulls PyTorch (~2 GB image).
#   requirements-prod.txt  slim — no sentence-transformers. The embedder
#                          degrades gracefully and the retriever returns no
#                          chunks, so the tutor still runs on personalization
#                          and conversation history alone.
#
# Slim is the default so any plain `docker build` produces the deployable
# shape — Render's blueprint spec has no way to pass --build-arg, so the
# default is what it gets. Compose opts into the full set explicitly.
ARG REQUIREMENTS=requirements-prod.txt

COPY requirements.txt requirements-prod.txt ./
RUN pip install --no-cache-dir -r ${REQUIREMENTS}

COPY ./app ./app

# Migrations have to be in the image for the entrypoint to apply them. They
# were previously absent, so the built image could only ever talk to a database
# somebody had migrated by hand.
COPY alembic.ini .
COPY ./alembic ./alembic

COPY entrypoint.sh .
RUN chmod +x entrypoint.sh

ENTRYPOINT ["./entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
