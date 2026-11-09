FROM python:3.10-slim

WORKDIR /app

# Instalar herramientas básicas de red y utilidades
RUN apt-get update && apt-get install -y \
    iputils-ping \
    net-tools \
    socat \
    && rm -rf /var/lib/apt/lists/*

# Copiar primero requirements para aprovechar la caché de capas de Docker
COPY requirements.txt .

# Instalar dependencias previas (AirSim exige numpy antes de instalarse)
RUN pip install --no-cache-dir numpy msgpack-rpc-python

# Instalar dependencias de Python (pymavlink, flask, etc.)
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el resto del proyecto
COPY . .

# Dar permisos de ejecución al entrypoint
RUN chmod +x entrypoint.sh

# Ejecutar el script entrypoint por defecto
ENTRYPOINT ["/app/entrypoint.sh"]
