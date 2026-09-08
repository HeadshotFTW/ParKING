FROM python:3.12-slim AS native-builder

WORKDIR /build

RUN apt-get update \
    && apt-get install -y --no-install-recommends g++ \
    && rm -rf /var/lib/apt/lists/*

COPY native/service_fee.cpp .
RUN g++ -std=c++17 -O0 -shared -fPIC service_fee.cpp -o libservice_fee.so


FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends wget ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY --from=native-builder /build/libservice_fee.so /app/native/libservice_fee.so

RUN mkdir -p /app/data /app/data/avatars /app/exports \
    && sed -i 's/\r$//' /app/start.sh \
    && chmod +x /app/start.sh

EXPOSE 5000 5001

CMD ["/app/start.sh"]
