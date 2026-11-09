# Gestión Multi‐Entorno en AirSim (Orquestador Launcher)

Uno de los mayores desafíos logísticos al operar múltiples arquitecturas de vuelo (**PX4** y **ArduPilot**) sobre el mismo simulador (**Unreal Engine + AirSim**) es la gestión del archivo de configuración `settings.json`.

> [!IMPORTANT]
> AirSim lee obligatoriamente este archivo desde la ruta raíz de Windows (`Documentos/AirSim/settings.json`) en el instante exacto en que se inicia el motor gráfico. Modificar este archivo a mano cada vez que se cambia de firmware es propenso a errores y poco escalable.

Para solucionar este cuello de botella, desarrollamos un **Lanzador Interactivo (Launcher)** en Python que actúa como administrador de perfiles y orquestador del entorno.

---

## 1. Arquitectura del Orquestador

El sistema gestor se compone de tres archivos clave ubicados en la raíz del proyecto:

* **`settings_px4.json`**: Plantilla base con los puertos de telemetría (UDP 14540, TCP 4560) y el modo *LockStep* requeridos específicamente por el ecosistema PX4.
* **`settings_ardupilot.json`**: Plantilla base configurada con el `LocalHostIp: 0.0.0.0` y los puertos (UDP 9003/9002) requeridos por el SITL de ArduPilot.
* **`launcher.py`**: Script inteligente en Python que automatiza el proceso de despliegue y sobrescritura de configuraciones.

---

## 2. Flujo de Funcionamiento

Al ejecutar el script en la terminal mediante el comando `python launcher.py`, se despliega un menú interactivo. Al seleccionar un entorno de simulación, el script ejecuta la siguiente secuencia de forma automática:

1. **Detección de Entorno:** El script localiza automáticamente el directorio de documentos del usuario (independientemente del PC o si se está ejecutando desde Linux/WSL o Windows nativo).
2. **Carga de Perfil:** Toma la plantilla `.json` correspondiente a la arquitectura seleccionada.
3. **Inyección de Configuración:** Sobreescribe el archivo `settings.json` oficial de AirSim.

> [!TIP]
> Este flujo profesional asegura que, cuando el usuario presiona "Play" en Unreal Engine, el entorno 3D ya está preconfigurado para escuchar y transmitir por los puertos correctos del firmware seleccionado. Esto previene colisiones de red o simuladores congelados por pérdida de paquetes.

---

## 3. Código Fuente del Launcher (`launcher.py`)

A continuación se presenta el código de la lógica base de selección y reemplazo de configuraciones:

```python
import os
import sys
import shutil
import platform

# 1. Detectar el entorno (Windows o Ubuntu/WSL)
if os.name == 'nt':
    USER_HOME = os.environ.get("USERPROFILE", os.path.expanduser("~"))
else:
    # Extracción dinámica del usuario de Windows desde WSL
    ruta_actual = os.path.abspath(__file__)
    if "/mnt/c/Users/" in ruta_actual:
        partes = ruta_actual.split("/")
        usuario_windows = partes[4]
        USER_HOME = f"/mnt/c/Users/{usuario_windows}"
    else:
        # Fallback de seguridad
        USER_HOME = "/mnt/c/Users/matias.hinrichsen"

# 2. Definición de rutas absolutas
AIRSIM_PATH = os.path.join(USER_HOME, "Documents", "AirSim")
SETTINGS_DESTINO = os.path.join(AIRSIM_PATH, "settings.json")
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

TEMPLATE_PX4 = os.path.join(CURRENT_DIR, "settings_px4.json")
TEMPLATE_ARDUPILOT = os.path.join(CURRENT_DIR, "settings_ardupilot.json")

def aplicar_configuracion(entorno):
    """
    Función encargada de sobreescribir la configuración de AirSim
    según el firmware de vuelo seleccionado.
    """
    origen = TEMPLATE_PX4 if entorno == "PX4" else TEMPLATE_ARDUPILOT
    
    if not os.path.exists(origen):
        print(f"\n[ERROR] No se encontró la plantilla: {origen}")
        return

    if not os.path.exists(AIRSIM_PATH):
        os.makedirs(AIRSIM_PATH)

    try:
        shutil.copy2(origen, SETTINGS_DESTINO)
        print("\n" + "="*50)
        print(f"✅ ¡ÉXITO! Configuración de {entorno} aplicada.")
        print(f"Archivo actualizado en: {SETTINGS_DESTINO}")
        print("="*50)
        print("👉 Ya puedes darle 'Play' a Unreal Engine.\n")
    except Exception as e:
        print(f"\n[ERROR] Ocurrió un error al copiar el archivo: {e}")

def mostrar_menu():
    """
    Despliega el menú CLI interactivo para el usuario.
    """
    while True:
        print("\n🚁 SELECTOR DE SIMULADOR - AIRSIM 🚁")
        print("Elige el entorno antes de iniciar Unreal Engine:")
        print("1. Configurar para PX4")
        print("2. Configurar para ArduPilot")
        print("3. Salir")
        
        opcion = input("\nIngresa el número de tu opción (1, 2 o 3): ")
        
        if opcion == '1':
            aplicar_configuracion("PX4")
            break
        elif opcion == '2':
            aplicar_configuracion("ArduPilot")
            break
        elif opcion == '3':
            print("Saliendo sin hacer cambios...")
            break
        else:
            print("⚠️ Opción inválida, por favor intenta de nuevo.")

if __name__ == '__main__':
    mostrar_menu()
```
