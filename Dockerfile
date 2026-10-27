FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# Copy source code
COPY config.py server.py ./
COPY core/ core/
COPY static/ static/

EXPOSE 8000

ENV PYTHONUNBUFFERED=1
ENV MT5_MODE=bridge
ENV MT5_BRIDGE_URL=http://host.docker.internal:8081
ENV WEB_HOST=0.0.0.0
ENV WEB_PORT=8000

CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
