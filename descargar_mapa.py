import os
import math
import requests
import time

# Coordenadas de tu simulador AirSim (UBO, Santiago de Chile)
LAT = -33.467225
LON = -70.657605

# Niveles de zoom a descargar (14 es vista lejana, 19 es vista cercana)
ZOOM_MIN = 14
ZOOM_MAX = 19

def grados_a_tile(lat, lon, zoom):
    """Convierte coordenadas GPS a números de cuadrícula (Tile X, Y) de OpenStreetMap"""
    lat_rad = math.radians(lat)
    n = 2.0 ** zoom
    xtile = int((lon + 180.0) / 360.0 * n)
    ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    return (xtile, ytile)

def descargar_tiles():
    print("Iniciando descarga de mapa para modo Offline...")
   # Nos "disfrazamos" de un navegador Google Chrome estándar para evitar el bloqueo 403
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'image/png,image/*;q=0.8,*/*;q=0.5'
    }
    # La carpeta base será la carpeta 'static' que creaste antes
    base_dir = "static/tiles"

    for zoom in range(ZOOM_MIN, ZOOM_MAX + 1):
        x_centro, y_centro = grados_a_tile(LAT, LON, zoom)
        
        # Descargaremos una cuadrícula más amplia según el nivel de zoom para evitar fondos grises
        if zoom <= 15:
            rango = 3  # 7x7 imágenes
        elif zoom <= 17:
            rango = 4  # 9x9 imágenes
        else:
            rango = 5  # 11x11 imágenes 
        
        for x in range(x_centro - rango, x_centro + rango + 1):
            for y in range(y_centro - rango, y_centro + rango + 1):
                
                # Crea la ruta de carpetas, por ejemplo: static/tiles/18/42000/
                ruta_carpeta = f"{base_dir}/{zoom}/{x}"
                os.makedirs(ruta_carpeta, exist_ok=True)
                
                ruta_archivo = f"{ruta_carpeta}/{y}.png"
                
                # Si la imagen no existe, la descarga
                if not os.path.exists(ruta_archivo):
                    url = f"https://tile.openstreetmap.org/{zoom}/{x}/{y}.png"
                    try:
                        respuesta = requests.get(url, headers=headers)
                        if respuesta.status_code == 200:
                            with open(ruta_archivo, 'wb') as f:
                                f.write(respuesta.content)
                            print(f"Descargado: Zoom {zoom} | Cuadrícula X:{x} Y:{y}")
                            time.sleep(0.3) # Pausa de cortesía para no saturar el servidor web
                        else:
                            print(f"Error {respuesta.status_code} en: {url}")
                    except Exception as e:
                        print(f"Error de conexión: {e}")
                else:
                    print(f"El archivo ya existe: Zoom {zoom} | X:{x} Y:{y}")
                    
    print("\n--- DESCARGA DE MAPA LOCAL COMPLETADA ---")

if __name__ == "__main__":
    descargar_tiles()