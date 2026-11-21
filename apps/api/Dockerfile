FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN python -m pip install --no-cache-dir -r requirements.lock && python -m pip install --no-deps .
USER 65532:65532
EXPOSE 8000
CMD ["python", "-m", "uvicorn", "opencode_api.app:app", "--host", "0.0.0.0", "--port", "8000"]
