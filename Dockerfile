FROM python:3.11-slim

WORKDIR /app

COPY . /app/

# Instalar pacotes do sistema para mysqlclient
RUN apt-get update && apt-get install -y \
    default-libmysqlclient-dev \
    build-essential \
    pkg-config \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get remove -y build-essential pkg-config \
    && apt-get autoremove -y \
    && apt-get clean

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 4433

CMD ["gunicorn", "SOLANA:app", \
     "--certfile=/etc/ssl/myapp/python-server.crt", \
     "--keyfile=/etc/ssl/myapp/python-server.key", \
     "--bind=0.0.0.0:4433"]

