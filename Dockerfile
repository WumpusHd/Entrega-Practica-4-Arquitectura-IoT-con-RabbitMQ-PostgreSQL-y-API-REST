FROM python:3.11-slim
WORKDIR /app
RUN pip install pika psycopg2-binary flask requests