import os
import sys
import shutil
import platform
import time
import subprocess

# Detectar si estamos en Windows o en Ubuntu (WSL)
if os.name == 'nt':
    # Estamos en Windows
    USER_HOME = os.environ.get("USERPROFILE", os.path.expanduser("~"))
else:
    # Asumimos que estamos en Ubuntu / WSL
    # Extraemos el usuario de Windows basándonos en la ruta actual del script
    # Ejemplo de ruta en WSL: /mnt/c/Users/matias.hinrichsen/Desktop/...
    ruta_actual = os.path.abspath(__file__)
    if "/mnt/c/Users/" in ruta_actual:
        partes = ruta_actual.split("/")
        usuario_windows = partes[4] # matias.hinrichsen
        USER_HOME = f"/mnt/c/Users/{usuario_windows}"
    else:
        # Fallback en caso raro
        USER_HOME = "/mnt/c/Users/matias.hinrichsen"

AIRSIM_PATH = os.path.join(USER_HOME, "Documents", "AirSim")
SETTINGS_DESTINO = os.path.join(AIRSIM_PATH, "settings.json")

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_PX4 = os.path.join(CURRENT_DIR, "settings_px4.json")
TEMPLATE_ARDUPILOT = os.path.join(CURRENT_DIR, "settings_ardupilot.json")

def aplicar_configuracion(entorno):
    origen = TEMPLATE_PX4 if entorno == "PX4" else TEMPLATE_ARDUPILOT
    
    if not os.path.exists(origen):
        print(f"\n[ERROR] Archivo de plantilla de configuración no encontrado: {origen}")
        return

    if not os.path.exists(AIRSIM_PATH):
        os.makedirs(AIRSIM_PATH)

    try:
        shutil.copy2(origen, SETTINGS_DESTINO)
            
        print("\n" + "="*60)
        print(f"[SYSTEM] Configuración de entorno '{entorno}' aplicada exitosamente.")
        print(f"[SYSTEM] Destino actualizado: {SETTINGS_DESTINO}")
        print("="*60)
        
        # --- AUTOMATIZACIÓN DE DESPLIEGUE ---
        print("\n[ORQUESTADOR] Iniciando automatización de despliegue...")
        
        # Función auxiliar para abrir programas de Windows sin importar si estamos en Windows o WSL
        def start_windows_app(app_path, title=""):
            if os.name == 'nt':
                subprocess.Popen(["cmd.exe", "/c", "start", title, app_path])
            else:
                # En WSL, cmd.exe debe llamarse con su ruta completa o usar cmd.exe si hay interop
                subprocess.Popen(["/mnt/c/Windows/System32/cmd.exe", "/c", "start", title, app_path])
                
        # Función auxiliar para abrir la terminal del SITL
        def start_sitl_terminal(script_path, entorno_name):
            if os.name == 'nt':
                # Desde Windows, abrimos wsl bash
                subprocess.Popen(["cmd.exe", "/c", "start", '""', "wsl", "bash", script_path])
            else:
                # Desde WSL, usamos cmd.exe de Windows para abrir una nueva consola con WSL
                subprocess.Popen(["/mnt/c/Windows/System32/cmd.exe", "/c", "start", '""', "wsl", "bash", script_path])

        # 1. Iniciar Unreal Engine
        print("[ORQUESTADOR] Paso 1: Abriendo entorno virtual (Unreal Engine)...")
        unreal_path = r"C:\Lab\prueba 5\prueba 5\Windows\MyProject.exe"
        start_windows_app(unreal_path)
        
        print("[ORQUESTADOR] Esperando 15 segundos para la carga del mapa 3D...")
        time.sleep(15)
        
        # 2. Iniciar QGroundControl
        print("[ORQUESTADOR] Paso 2: Abriendo estación terrena QGroundControl...")
        qgc_path = r"C:\ProgramData\Microsoft\Windows\Start Menu\Programs\QGroundControl\QGroundControl.lnk"
        start_windows_app(qgc_path)
        
        print("[ORQUESTADOR] Esperando 10 segundos para conexión de telemetría...")
        time.sleep(10)
        
        # 3. Iniciar Cerebro SITL
        print(f"[ORQUESTADOR] Paso 3: Inicializando Cerebro SITL ({entorno})...")
        script_sitl = "start_px4.sh" if entorno == "PX4" else "start_ardupilot.sh"
        ruta_script_sitl = os.path.join(CURRENT_DIR, script_sitl)
        
        # Convertir ruta de Windows a formato WSL para que bash la encuentre
        if os.name == 'nt':
            drive, tail = os.path.splitdrive(ruta_script_sitl)
            wsl_ruta = f"/mnt/{drive.replace(':', '').lower()}{tail.replace(chr(92), '/')}"
        else:
            wsl_ruta = ruta_script_sitl
            
        start_sitl_terminal(wsl_ruta, entorno)
        
        print("[ORQUESTADOR] Esperando 15 segundos para inicialización del SITL...")
        time.sleep(15)

        # 4. Iniciar Script de Misión (Comandante)
        print(f"[ORQUESTADOR] Paso 4: Lanzando Comandante de Misión ({entorno})...")
        script_mision = "mision_autonoma.py" if entorno == "PX4" else "mision_ardupilot.py"
        ruta_mision = os.path.join(CURRENT_DIR, script_mision)
        
        if os.name == 'nt':
            os.system(f'python "{ruta_mision}"')
        else:
            os.system(f'python3 "{ruta_mision}"')
            
        print("\n[SUCCESS] Secuencia de orquestación completada con éxito.")
        
    except Exception as e:
        error_msg = str(e)
        print(f"\n[ERROR] Excepción detectada durante la orquestación: {error_msg}")
        if "Exec format error" in error_msg or "Errno 8" in error_msg:
            print("="*60)
            print("[ALERTA CRÍTICA DE WSL2]")
            print("Tu terminal de Linux (WSL) ha perdido la conexión con Windows (error de interop).")
            print("Para solucionarlo, DEBES hacer lo siguiente:")
            print("1. Abre una terminal de Windows PowerShell (NO Ubuntu).")
            print("2. Escribe el comando:  wsl --shutdown  y presiona Enter.")
            print("3. Vuelve a abrir tu terminal de Ubuntu y ejecuta python3 launcher.py nuevamente.")
            print("="*60)

def mostrar_menu():
    while True:
        print("\n--- SELECTOR DE ENTORNO DE SIMULACIÓN (AIRSIM) ---")
        print("Seleccione el controlador de vuelo a inicializar:")
        print("1. Cargar configuración para PX4 (SITL)")
        print("2. Cargar configuración para ArduPilot (SITL)")
        print("3. Salir")
        
        opcion = input("\nIngrese una opción (1, 2 o 3): ")
        
        if opcion == '1':
            aplicar_configuracion("PX4")
            break
        elif opcion == '2':
            aplicar_configuracion("ArduPilot")
            break
        elif opcion == '3':
            print("[SYSTEM] Finalizando proceso. No se realizaron cambios en la configuración.")
            break
        else:
            print("[WARNING] Parámetro inválido. Ingrese un valor numérico válido.")

if __name__ == '__main__':
    mostrar_menu()
