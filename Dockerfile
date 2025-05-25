FROM python:3.11-slim
ENV PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY . .

RUN pip install -r api/requirements.txt

ENV PORT=8000
EXPOSE $PORT

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
