FROM python:3.12-slim

WORKDIR /app
COPY src/ ./src/
COPY api/ ./api/

ENV PYTHONPATH=/app
EXPOSE 8000

CMD ["python", "-m", "src.WebAPI.composition_root"]
