# Guía de Edición Básica (Modificando la Misión)

Esta guía rápida te enseñará cómo y dónde modificar los parámetros más importantes de tu simulación, como las rutas de vuelo, la altitud, el punto de partida y los mapas del Dashboard.

---

## 1. Cambiar la Altura de Vuelo
El dron tiene configurada una altitud de crucero a la que sube antes de empezar a mapear.

- **Archivos a modificar:** `mision_autonoma.py` (PX4) o `mision_ardupilot.py` (ArduPilot).
- **Dónde buscar:** En las primeras líneas del archivo, busca la sección `# --- PARÁMETROS DE VUELO Y TELEMETRÍA ---`.
- **Qué cambiar:**
  ```python
  ALTURA_SEGURA = -115.0  # Altitud de seguridad en metros
  ```
  *(Nota: Se usan valores negativos porque el sistema utiliza la convención NED: Norte, Este, Abajo. Por lo tanto, -115 significa 115 metros hacia arriba).*

---

## 2. Cambiar la Ruta de Vuelo (Waypoints)
Si quieres que el dron haga un cuadrado más grande, un triángulo, o explore otros lugares, debes editar sus coordenadas.

- **Archivos a modificar:** `mision_autonoma.py` o `mision_ardupilot.py`.
- **Dónde buscar:** Ve hacia el medio del archivo, dentro de la función `ejecutar_vuelo()`, busca la variable `puntos_ruta`.
- **Qué cambiar:**
  ```python
  # Matriz de ruta planificada
  puntos_ruta = [
      (200.0, 0.0, ALTURA_SEGURA), 
      (200.0, 200.0, ALTURA_SEGURA),
      # (Posición X, Posición Y, Altura)
      # ...
  ]
  ```
  * X (positivo es al Norte, negativo es al Sur)
  * Y (positivo es al Este, negativo es al Oeste)
  * Z (la altura, por defecto usa tu variable `ALTURA_SEGURA`).

---

## 3. Cambiar el Origen Geográfico del Dashboard (El Mapa Base)
El mapa geoespacial en tu Dashboard web asume que el dron despegó desde un punto GPS específico en el mundo real. Si cambias de escenario en Unreal (por ejemplo, pasas de Santiago a una costa en Valparaíso), querrás que el mapa del Dashboard refleje esa costa.

- **Archivo a modificar:** `templates/index.html`.
- **Dónde buscar:** Casi al final del archivo, en la sección de `<script>`, busca `MAPA GEOESPACIAL (LEAFLET)`.
- **Qué cambiar:**
  ```javascript
  const ORIGEN_LAT = -33.467225; // Latitud de tu nuevo origen
  const ORIGEN_LON = -70.657605; // Longitud de tu nuevo origen
  ```
  *Busca las coordenadas reales en Google Maps y pégalas aquí.*

### Cambiar el estilo visual del Mapa (Modo Oscuro)
Si el mapa satelital es muy brillante y quieres quitarle el "estilo militar nocturno" para ver los colores reales:
- **Dónde buscar:** En `index.html`, en la parte superior dentro de la etiqueta `<style>`, busca `#mapa-container`.
- **Qué cambiar:** Borra o comenta la línea que dice `filter: invert(100%)...`.

---

## 4. Cambiar el Punto de Partida del Dron en Unreal Engine
Para hacer que el dron aparezca en una montaña, en un edificio o en un barco dentro del escenario 3D:

- **Herramienta a usar:** El Editor de Unreal Engine 5.
- **Qué cambiar:** 
  1. Abre tu nivel/mapa en Unreal Engine.
  2. En la lista de objetos de la escena (Outliner), busca un objeto llamado **Player Start**.
  3. Muévelo, súbelo o gíralo hacia donde quieras que el dron aparezca cuando le des a "Play". AirSim usará exactamente ese punto como el origen `(X:0, Y:0, Z:0)` de la misión.

---

## 5. Descargar Mapas Offline para el Dashboard (Radares)
El mapa satelital del Dashboard funciona sin internet (está 100% offline). Por lo tanto, si cambiaste las coordenadas de origen en el paso 3, **debes descargar las imágenes satelitales** de ese nuevo lugar geográfico para que aparezcan como fondo.

- **Herramienta a usar:** El script `descargar_mapa.py`.
- **Ruta de las Imágenes:** Las fotos del mapa se guardan automáticamente en la carpeta `static/tiles/`.
- **Pasos para descargar un mapa nuevo:**
  1. Abre el archivo `descargar_mapa.py` en tu editor de código.
  2. Busca estas variables cerca del inicio:
     ```python
     LATITUD_CENTRO = -33.467225
     LONGITUD_CENTRO = -70.657605
     ```
  3. Cambia esos valores por las mismas coordenadas GPS del nuevo lugar que pusiste en tu `index.html`.
  4. Guarda el archivo y ejecútalo en la terminal de comandos de Windows:
     ```bash
     python descargar_mapa.py
     ```
  5. Verás en la consola cómo el script comienza a descargar decenas de pequeños cuadros (imágenes `.png`). Cuando termine, todas quedarán perfectamente acomodadas en las carpetas `static/tiles/{zoom}/{x}/{y}.png`. 
  6. ¡Listo! Al volver a abrir tu Dashboard, el nuevo mapa cargará instantáneamente.
