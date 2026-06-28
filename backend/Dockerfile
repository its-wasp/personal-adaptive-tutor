FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

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
