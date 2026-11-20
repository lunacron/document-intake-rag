FROM python:3.12-slim
WORKDIR /code
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && python -m spacy download en_core_web_sm
COPY app app
# The app runs as a non-root user (see docker-compose.yml), so give it a writable model cache.
ENV HF_HOME=/hf HOME=/tmp
RUN mkdir /hf && chown 1000:1000 /hf
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
