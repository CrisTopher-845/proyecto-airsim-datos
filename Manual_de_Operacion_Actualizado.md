# Manual de Operación: Entorno de Simulación Autónoma Avanzado (AirSim + PX4 / ArduPilot)

## 1. Visión General del Sistema
Este entorno es un **"Gemelo Digital"** totalmente automatizado compuesto por cuatro bloques principales que trabajan en perfecta sincronía. A diferencia de versiones anteriores, este sistema cuenta con un **Orquestador** que arranca y vincula todos los procesos de forma autónoma:

- **Unreal Engine 5 + AirSim (El Mundo):** Renderiza la física hiperrealista, el clima y el modelo 3D del dron.
- **SITL en Ubuntu (El Cerebro):** El software de control de vuelo (PX4 o ArduPilot) que calcula la física y dinámica de vuelo.
- **Script de Python (El Comandante):** Orquesta la misión, envía las coordenadas de vuelo, atrapa señales de emergencia y recolecta telemetría.
- **Dashboard Web + QGroundControl (La Estación Terrena):** Interfaces para monitorear la ruta en tiempo real. Ahora se abren automáticamente al iniciar la simulación.

---

## 2. Estructura de Archivos y Carpetas
Todos los archivos del proyecto deben estar ubicados en la carpeta principal:
`c:\Users\matias.hinrichsen\Desktop\cris.AirSim\proyecto-airsim-datos\`

### Archivos Principales
1. **`launcher.py` (NUEVO):**
   *Ruta:* `c:\Users\matias.hinrichsen\Desktop\cris.AirSim\proyecto-airsim-datos\launcher.py`
   El **Orquestador Automático**. Es el único archivo que el operador necesita ejecutar. Se encarga de abrir Unreal, inyectar configuraciones, lanzar el SITL, abrir QGroundControl, el Dashboard y la misión.
2. **`mision_autonoma.py`:** 
   *Ruta:* `c:\Users\matias.hinrichsen\Desktop\cris.AirSim\proyecto-airsim-datos\mision_autonoma.py`
   Script de misión exclusivo para **PX4**. Arranca el servidor web en el puerto `5001`.
3. **`mision_ardupilot.py`:**
   *Ruta:* `c:\Users\matias.hinrichsen\Desktop\cris.AirSim\proyecto-airsim-datos\mision_ardupilot.py`
   Script de misión exclusivo para **ArduPilot**. Arranca el servidor web en el puerto `5000`.
4. **`start_px4.sh` / `start_ardupilot.sh`:**
   *Rutas:* `...\start_px4.sh` / `...\start_ardupilot.sh`
   Scripts de shell nativos de Linux invocados por el orquestador para encender los "Cerebros" SITL.
5. **`mision_mapeo_final.csv` / `mision_mapeo_ardupilot.csv`:**
   *Rutas:* `...\mision_mapeo_final.csv` / `...\mision_mapeo_ardupilot.csv`
   Archivos autogenerados donde se guarda la telemetría histórica tras cada vuelo.

### Carpetas
- **`templates/`:** 
  *Ruta:* `c:\Users\matias.hinrichsen\Desktop\cris.AirSim\proyecto-airsim-datos\templates\`
  Contiene el diseño visual del Dashboard (`index.html`).

---

## 3. El Archivo Maestro de Configuración (`settings.json`)
El Orquestador gestiona esto por ti, inyectando automáticamente la plantilla correspondiente (`settings_px4.json` o `settings_ardupilot.json`) hacia la carpeta de Windows (`Documentos\AirSim\settings.json`). 

- Define que el vehículo es un multirotor.
- Habilita las IPs y puertos necesarios (Ej: UDP 14540 para PX4, o TCP 5760/5762 para ArduPilot).

---

## 4. Secuencia de Encendido (Automatizada)
Gracias a la nueva arquitectura, la secuencia de encendido manual ha quedado obsoleta. El nuevo procedimiento de vuelo consta de **un solo paso**:

### Paso Único: Lanzar el Orquestador
1. Abre tu terminal de **Ubuntu (WSL)**.
2. Navega a la carpeta del proyecto:
   ```bash
   cd /mnt/c/Users/matias.hinrichsen/Desktop/cris.AirSim/proyecto-airsim-datos
   ```
3. Ejecuta el launcher:
   ```bash
   python3 launcher.py
   ```
4. El sistema mostrará un menú. **Ingresa 1 para PX4 o 2 para ArduPilot.**

A partir de este momento, puedes soltar el teclado. **El sistema realizará todo el proceso de forma automática, con una única excepción:** si eliges ArduPilot, la conexión en QGroundControl deberá hacerse de forma manual (como se ha configurado por diseño).

El Orquestador hará lo siguiente:
- Copiará el `settings.json` correcto.
- Abrirá **Unreal Engine 5**. *(Nota: Unreal Engine se congelará intencionalmente a la espera de la conexión del cerebro).*
- Lanzará una terminal secundaria en Ubuntu iniciando el firmware **SITL** correspondiente. *(Al completarse, Unreal Engine se descongelará).*
- Abrirá **QGroundControl**. *(Recuerda: Si elegiste ArduPilot, aquí debes realizar tu conexión manual TCP en el puerto 5763).*
- Ejecutará el script de misión, abrirá automáticamente tu **Navegador Web** con el Dashboard, y el dron despegará (hasta 115m de altura).

---

## 5. Protocolo de Emergencia (Abortar Misión)
El sistema cuenta con un interceptor de señales de sistema (SIGINT) a prueba de fallos. 
Si necesitas abortar el vuelo antes de que termine su ruta programada:

1. Haz clic en la **consola negra que muestra los datos de telemetría** (`[TELEMETRY] T: 45.2s...`).
2. Presiona `Ctrl + C`.
3. Verás el mensaje rojo `[SYSTEM][EMERGENCIA] Comando RTL enviado al vehículo.`.
4. El dron abandonará la misión inmediatamente, dará media vuelta y aterrizará a salvo en el punto de inicio (Return To Launch). El servidor web se apagará de forma segura.

---

## 6. Interpretación de la Telemetría (Dashboard Web)
- **Valores X, Y, Z:** Indican la posición actual del dron. Un valor `Z = -115` indica que el dron ha alcanzado la altura de crucero.
- **Velocidades (Vel_X, Vel_Y):** Si permanecen en 0.0 mientras el dron está en el aire y no ha terminado la ruta, el dron está pausado o rechazando coordenadas.

---

## 7. Matriz de Resolución de Problemas (Troubleshooting)

| Síntoma | Causa Probable | Acción Correctiva |
| :--- | :--- | :--- |
| **Consola del SITL se cierra inmediatamente o tira error `command not found`** | Problemas cargando el `PATH` o el `.bashrc` en la sub-terminal no-interactiva de Ubuntu. | El orquestador ya usa rutas absolutas y carga el PATH directamente en el `.sh` para evitarlo. Si ocurre, verificar las rutas internas del archivo `start_px4.sh` o `start_ardupilot.sh`. |
| **QGroundControl muestra `Unsupported main mode`** | ArduPilot/PX4 no recibió suficientes coordenadas de seguridad antes del armado. | Ignorar si es temporal. El script reintentará armar automáticamente hasta tener posición. |
| **Unreal Engine se queda "congelado" permanentemente** | El firmware SITL (PX4/ArduPilot) falló al arrancar y no pudo conectarse con Unreal Engine. | Revisa la terminal negra del SITL. Si falló, ciérrala y usa `wsl --shutdown` en PowerShell para limpiar procesos colgados. |
| **El dron no arma y la consola dice "Armado rechazado" repetidas veces** | El filtro EKF de ArduPilot/PX4 aún no ha establecido un origen GPS válido. | **Esperar.** Es un mecanismo de seguridad vital. Tomará entre 15 y 30 segundos. El script es paciente y armará solo cuando sea seguro. |
| **El navegador no se abre automáticamente** | El interceptor de comandos de WSL hacia Windows falló. | Abre el navegador manualmente. **PX4:** `http://127.0.0.1:5001` | **ArduPilot:** `http://127.0.0.1:5000`. |
| **Se requiere limpiar el sistema entre simulaciones** | Puertos bloqueados por ejecuciones anteriores. | En PowerShell, ejecuta: `wsl --shutdown`. Luego cierra QGC y Unreal Engine y vuelve a empezar. |

---
*Manual generado para la arquitectura automatizada v2.0.*
