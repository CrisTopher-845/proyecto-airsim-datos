# Documentación de Integración con Docker (AirSim SITL)

Este documento detalla el proceso, la arquitectura y las decisiones de diseño tomadas para la integración del entorno de simulación autónomo (AirSim + PX4/ArduPilot) con **Docker**. 

La versión contenida en este directorio (`proyecto-airsim-docker`) es un *fork* o copia aislada del proyecto original.

---

## 1. Motivación y Decisión de Arquitectura (La "Copia Segura")

Durante la fase de desarrollo, el sistema original ejecutaba las misiones autónomas (scripts de Python) directamente sobre el entorno host del usuario (Windows/WSL). 

**Problema:** A medida que el proyecto crece, la gestión de dependencias (PyMavlink, Flask, utilidades del sistema) se vuelve frágil y depende completamente del entorno local del usuario, dificultando su portabilidad a otros computadores.
**Solución:** Contenerizar los "Comandantes de Misión" (los scripts de Python que se conectan al SITL y a la estación terrena web) usando Docker.

**¿Por qué hicimos una copia del proyecto?**
Para garantizar la **continuidad operacional**. El proyecto original funcionaba a la perfección. Intervenir sus archivos directamente corría el riesgo de romper el entorno funcional de producción. Al crear una carpeta copia exclusiva para la integración Docker, logramos un entorno de pruebas seguro (Sandbox) donde, ante cualquier error crítico, el trabajo base original seguía intacto. Hoy, ambas versiones funcionan a la perfección de forma independiente.

---

## 2. Arquitectura de Despliegue (Docker)

El sistema ahora cuenta con un orquestador inteligente (`launcher.py`) que coordina el ecosistema completo (Simulador 3D, Estación Terrena, Cerebro de Vuelo y el Contenedor Docker).

### Componentes Clave:
1. **Dockerfile:** Basado en `python:3.9-slim`, instala dependencias esenciales del sistema (`socat`, `iproute2`) y las librerías de Python requeridas (`pymavlink`, `flask`, `python-dotenv`).
2. **docker-compose.yml:** Define el servicio `orquestador` mapeando los puertos `5000-5020` para la estación terrena web (Dashboard Flask). Soporta paso dinámico de variables de entorno (como `$ENTORNO_SITL`) y sincronización de volúmenes para que las modificaciones a los scripts no requieran reconstruir la imagen de Docker constantemente.
3. **entrypoint.sh:** Un script de Bash que actúa como guardia de tráfico. Analiza la variable de entorno `$ENTORNO_SITL` y decide internamente si ejecuta `mision_autonoma.py` (para PX4) o `mision_ardupilot.py` (para ArduPilot), resolviendo el enrutamiento interno (`host.docker.internal` para ArduPilot).

---

## 3. Desafíos Técnicos Resueltos

Durante el desarrollo de esta integración, superamos varios obstáculos de red y de interoperabilidad entre Windows y el Subsistema de Linux (WSL2):

### A. Ejecución Híbrida del Orquestador (Interoperabilidad WSL/Windows)
El usuario ejecuta el `launcher.py` desde una terminal de Ubuntu (WSL). Sin embargo, levantar contenedores Docker desde dentro de una consola de WSL utilizando el comando nativo de Linux a veces colisiona con Docker Desktop de Windows (provocando errores tipo *500 Internal Server Error* o *"docker command not found"*).
* **Solución:** Programamos el `launcher.py` para detectar si está corriendo en WSL. Si es así, convierte dinámicamente sus rutas de Linux (`/mnt/c/Users/...`) a formato Windows (`C:\Users\...`) y lanza el proceso llamando directamente al ejecutable de Windows (`cmd.exe /c docker-compose...`). Esto garantiza que el motor Docker Desktop procese la solicitud 100% de forma nativa.

### B. Herencia de Variables de Entorno
Necesitábamos indicarle al contenedor si correr PX4 o ArduPilot dinámicamente. Al cruzar la frontera entre WSL y CMD de Windows usando el comando `start`, las variables de entorno inyectadas con `set ENTORNO=...` a veces se perdían, forzando al contenedor a abrir PX4 por defecto, lo que bloqueaba puertos y confundía al usuario.
* **Solución:** Implementamos un sistema determinista en `launcher.py` que, justo antes de invocar a Docker, escribe físicamente un archivo oculto `.env` (ej: `ENTORNO_SITL=ArduPilot`). Docker Compose lee este archivo de forma nativa e independiente, asegurando que el comando llega limpio y sin pérdida de contexto.

### C. Colisiones de Puertos en el Dashboard Web (Flask)
Teníamos un error crítico donde ArduPilot (Opción 2) fallaba con `Address already in use (Port 5000)`. Inicialmente, para exponer los puertos internos del contenedor al host, utilizamos herramientas de forwarding como `socat`. Sin embargo, esto "robaba" el puerto 5000 del contenedor un milisegundo antes de que Flask intentara iniciar.
* **Solución:** Eliminamos los túneles innecesarios en `entrypoint.sh` y ordenamos a Flask, dentro de los scripts de Python, que expusiera su servidor nativamente hacia cualquier interfaz de red (`host='0.0.0.0'`). Esto elimina la necesidad de proxies intermedios y previene cualquier colisión.

### D. Apertura Automática del Dashboard (Hilo No-Daemon)
Anteriormente, al ejecutar los scripts directamente en el host, Python podía abrir el navegador web con `webbrowser.open()`. Al encapsular la misión dentro de Docker, el contenedor perdía acceso al escritorio gráfico del usuario, impidiendo que abriera ventanas de Windows.
* **Solución:** Delegamos esta tarea al orquestador principal (`launcher.py`). Creamos un hilo de procesamiento que espera 6 segundos (para dar tiempo a que Docker compile y levante) y luego dispara el comando para abrir el navegador en el host. Configuramos el hilo como `daemon=False` para asegurar que el script principal aguarde esos 6 segundos pacientemente antes de dar por terminado su ciclo de vida, evitando la muerte prematura del temporizador.

---

## 4. Instrucciones de Uso Final

El flujo operativo se ha vuelto inmensamente limpio y profesional:

1. **Prerrequisito:** Asegúrate de tener **Docker Desktop** abierto y corriendo en Windows.
2. Abre tu terminal de **Ubuntu (WSL2)**.
3. Posiciónate en la carpeta del proyecto.
4. Ejecuta:
   ```bash
   python3 launcher.py
   ```
5. Selecciona el entorno deseado (PX4 o ArduPilot).
6. El orquestador iniciará Unreal Engine, QGroundControl, el cerebro SITL de vuelo y, finalmente, construirá y lanzará el cerebro lógico dentro de un entorno estéril de **Docker**.
7. Pasados 6 segundos, tu navegador web se abrirá automáticamente apuntando a la IP correcta de Telemetría (`127.0.0.1:5001` para PX4 y `127.0.0.1:5000` para ArduPilot).

---
*Documentación generada al finalizar la Fase 3 de Integración DevOps del simulador autónomo.*
