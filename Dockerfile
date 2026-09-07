FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/data /app/exports \
    && sed -i 's/\r$//' /app/start.sh \
    && chmod +x /app/start.sh

EXPOSE 5000 5001

CMD ["/app/start.sh"]
