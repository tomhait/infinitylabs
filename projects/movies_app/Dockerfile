FROM python:3.14 AS builder

WORKDIR /app

COPY requirements.txt .

RUN pip install --user --no-cache-dir -r requirements.txt

FROM python:3.14

WORKDIR /app

COPY --from=builder /root/.local /root/.local

COPY src ./src
COPY README.txt .
COPY main.py .
COPY .template.env ./.env
COPY start.sh .

ENV PATH="/root/.local/bin:$PATH"

EXPOSE 8000

CMD ["./start.sh"]
