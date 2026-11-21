FROM python:3.13-slim
WORKDIR /app
COPY . .
RUN python -m pip install --no-cache-dir -r requirements.lock && python -m pip install --no-deps .
USER 65532:65532
CMD ["python", "-m", "opencode_worker"]
