# Informe Técnico Detallado: Integración de Sensores LiDAR en Ecosistemas Robóticos
**Contexto:** Arquitectura Autónoma (PX4 SITL, ROS 2, AirSim/Unreal Engine, Python)

Este informe técnico tiene como objetivo proporcionar un marco de referencia teórico y práctico para la futura expansión del proyecto mediante la integración de sensores LiDAR. Se abordan los conceptos fundamentales, la escalabilidad del sistema y las alternativas tanto físicas como simuladas.

---

## 1. Fundamentos: ¿Qué es la Tecnología LiDAR?

**LiDAR** (del inglés *Light Detection and Ranging*) es un sistema de teledetección óptica que utiliza haces de luz láser para medir distancias con precisión milimétrica.

### ¿Cómo funciona?
1. **Emisión (Time of Flight - ToF):** El sensor emite miles o millones de pulsos láser por segundo hacia el entorno.
2. **Recepción:** El láser choca contra una superficie (un edificio, un árbol, el suelo) y rebota de vuelta al sensor.
3. **Cálculo:** Un reloj de ultra-precisión calcula el tiempo exacto que tardó la luz en ir y volver. Sabiendo que la velocidad de la luz es constante, el sensor calcula la distancia exacta a la que se encuentra ese punto.
4. **Nube de Puntos (Point Cloud):** Al combinar la distancia calculada con el ángulo exacto en que se disparó el láser, el sensor genera una coordenada 3D `(X, Y, Z)`. La acumulación masiva de estas coordenadas genera lo que se conoce como una **Nube de Puntos**, una representación tridimensional y matemáticamente perfecta del mundo real.

---

## 2. Propósito: ¿Para qué sirve en nuestro Proyecto?

Actualmente, nuestro dron navega usando telemetría GPS y barométrica ciega (sabe dónde está, pero no sabe qué tiene alrededor). Integrar LiDAR abre la puerta a capacidades de autonomía de "Nivel 5":

1. **Evasión Dinámica de Obstáculos:** El dron podrá detectar muros, grúas o árboles en tiempo real y recalcular su ruta de manera autónoma, sin chocar, saltándose los waypoints estáticos que le inyecta nuestro orquestador en Python.
2. **Mapeo 3D de Precisión:** A diferencia de la fotogrametría clásica (basada en fotos), el láser penetra la vegetación. Es ideal para inspección de líneas eléctricas, topografía minera y agricultura de precisión.
3. **SLAM (Simultaneous Localization and Mapping):** Si el GPS falla o el dron entra a un túnel, el LiDAR permite que el sistema se "localice a sí mismo" construyendo un mapa tridimensional del entorno a medida que avanza.

---

## 3. Arquitectura y Escalabilidad: El Rol de ROS 2

Para integrar LiDAR de forma escalable, nuestro script base de Python debe evolucionar. Un sensor LiDAR genera Gigabytes de datos por minuto (millones de puntos por segundo). Procesar esto en un ciclo cerrado de Python es computacionalmente inviable.

Aquí es donde la arquitectura escala introduciendo **ROS 2 (Robot Operating System)**:
* **El Dron (PX4):** Sigue volando la misión básica.
* **El Sensor (LiDAR):** Publica la nube de puntos bruta (Data Raw).
* **El Cerebro (ROS 2):** Actúa como middleware. Toma la nube de puntos, la pasa por algoritmos de filtrado espacial (como Voxel Grids), algoritmos de mapeo (como Cartographer u OctoMap) y le devuelve a PX4 instrucciones de evasión instantáneas.

Nuestro proyecto está estructuralmente preparado para este salto, ya que PX4 y Python son módulos agnósticos que conviven perfectamente con ROS 2 bajo un entorno Docker.

---

## 4. Opciones de Hardware Físico (Para Adquisición Real)

Si el proyecto escala hacia la construcción de un dron físico, el hardware elegido debe tener un equilibrio entre peso (Payload) y compatibilidad con drivers.

### Escáneres 3D (Alta Resolución)
* **Livox (Mid-360 / Avia):** 
  * *Contexto:* Desarrollados por el ecosistema DJI. Tienen un escaneo no repetitivo (patrón floral) que llena áreas ciegas muy rápido.
  * *Ventajas:* Excelente relación peso/costo. Son los más populares hoy en día para mapeo forestal y urbano en drones ligeros.
  * *Integración:* Poseen drivers oficiales muy robustos en ROS 2 (`livox_ros_driver2`).
* **Velodyne VLP-16 (Puck):** 
  * *Contexto:* El estándar académico tradicional. Gira físicamente a alta velocidad cubriendo 360 grados.
  * *Ventajas:* Altamente confiable, la comunidad y la cantidad de foros para resolver errores de Velodyne en ROS y PX4 es infinita.
  * *Desventaja:* Costo elevado (aprox. $4,000 USD) y mayor consumo energético.

### Escáneres 2D (Sistemas Ligeros de Bajo Costo)
* **RPLiDAR (Series S y A):**
  * *Contexto:* Sensores que escanean en un único plano horizontal.
  * *Ventajas:* Cuestan menos de $400 USD. Pesan gramos.
  * *Uso en Proyecto:* No sirven para crear un mapa 3D de una ciudad, pero son perfectos para hacer **Evasión de Colisiones Frontales**. PX4 puede leerlos nativamente sin pasar por ROS 2, configurándolos simplemente como un "Distance Sensor" genérico vía MAVLink.

---

## 5. Integración del LiDAR Simulado (AirSim / Unreal Engine)

Antes de comprar hardware, la simulación nos permite validar los algoritmos de vuelo. AirSim soporta simulación LiDAR nativa.

### ¿Cómo funciona en el Simulador?
AirSim simula los rebotes láser utilizando un proceso matemático llamado **Raycasting** contra los objetos 3D y polígonos del mapa de Unreal Engine. Si el rayo virtual choca con una caja o una pared, registra la distancia.

### Pasos para integrarlo en el Proyecto Actual
Solo es necesario editar nuestro gestor de perfiles `settings.json` para "conectar" un LiDAR al dron virtual.

```json
"Sensors": {
    "Lidar_Frontal": {
        "SensorType": 6,
        "Enabled": true,
        "NumberOfChannels": 16,
        "RotationsPerSecond": 10,
        "PointsPerSecond": 100000,
        "X": 0, "Y": 0, "Z": -0.5,
        "Pitch": 0, "Roll": 0, "Yaw": 0,
        "DrawDebugPoints": true
    }
}
```
* *Explicación de Parámetros:* Se han definido 16 canales (equivalente al Velodyne VLP-16), girando a 10 Hz (RotationsPerSecond), montado 50 centímetros arriba del centro de masa del dron (`Z: -0.5` en sistema NED). Al activar `DrawDebugPoints`, Unreal mostrará puntitos de colores en vivo donde los láseres impactan.

---

## 6. Desafíos Técnicos de Simulación: El "Cuello de Botella" de Unreal

Integrar LiDAR en Unreal Engine presenta un desafío técnico masivo que debe ser considerado:

**El Consumo de CPU:** El proceso de disparar 100,000 rayos invisibles por segundo y calcular sus colisiones poligonales no es gestionado por la Tarjeta Gráfica (GPU), sino por el procesador central (CPU). 
Si se intenta simular un LiDAR de 64 canales de alta gama en un entorno urbano complejo en AirSim, el uso de CPU llegará rápidamente al 100%. 

**Consecuencia en nuestra Arquitectura:** Si Unreal Engine se satura y los FPS bajan de 30 fotogramas, la comunicación temporal entre AirSim y nuestro contenedor PX4 se romperá. Esto destruirá la directiva de seguridad **LockStep** (que mantiene el reloj del simulador sincronizado con el controlador de vuelo), provocando errores de inercia y caídas catastróficas del dron virtual.

---

## 7. Debate Arquitectónico para Escalar: ¿AirSim vs Gazebo?

Si a futuro el proyecto requiere entrenar Inteligencia Artificial sobre nubes de puntos súper densas, será imperativo evaluar si Unreal Engine es la plataforma adecuada.

| Ámbito de Análisis | Módulo AirSim (Unreal Engine) | Módulo Gazebo (Harmonic / Classic) |
| :--- | :--- | :--- |
| **Fidelidad Visual (Cámaras)** | **Ganador Absoluto.** Entornos fotorrealistas perfectos para algoritmos de Visión Computacional. | Básica. Geometrías simples, texturas planas. |
| **Computación LiDAR** | Altamente pesada (Basada en CPU). Propenso a ralentizar la simulación. | **Ganador Absoluto.** Aceleración total por GPU. Capaz de simular LiDARs de 128 canales sin sudar. |
| **Ecosistema y Conectividad** | Requiere wrappers y scripts intermedios para traducir a ROS 2. | Nativo. Publica directamente los mensajes estandarizados `sensor_msgs/PointCloud2` de ROS 2. PX4 SITL incluye modelos Gazebo por defecto. |

### Conclusión y Viabilidad
La integración LiDAR es **totalmente viable** con la base de arquitectura que hemos construido (Orquestador Python + Contenedores PX4 MAVLink). 

La hoja de ruta recomendada es:
1. **Fase 1 (Actual):** Iniciar con un LiDAR básico simulado (Ej. 16 canales) en nuestro entorno de **AirSim**, procesando tareas simples de evasión 2D a través de un script en Python adjunto al Orquestador.
2. **Fase 2 (Escalabilidad de Software):** Desplegar un contenedor paralelo de ROS 2. Dejar que Python administre el despegue/rutas, mientras ROS 2 absorbe los datos masivos del LiDAR para generar un mapa 3D (OctoMap) en tiempo real.
3. **Fase 3 (Escalabilidad de Hardware):** Adquirir un LiDAR Livox físico, montar un Companion Computer (Ej. Raspberry Pi o Jetson Nano) en el dron real, y transferir el mismo código ROS 2 y Python. Al ser agnóstico, el código no notará la diferencia entre el entorno simulado y la vida real.

---

## 8. Caso de Estudio Práctico: El Cuello de Botella RPC (AirSim)

Durante las pruebas de integración en laboratorio (Agosto 2026), se comprobó de manera empírica la limitación arquitectónica de AirSim mencionada en la sección 6.

### El Experimento
Se configuró un LiDAR virtual de alta densidad (16 canales, 50,000 puntos por segundo) en `settings_px4.json` y se activó la extracción de la nube de puntos (`getLidarData`) a 1 Hz mediante un hilo paralelo en Python. Adicionalmente, se exigió a Unreal Engine renderizar los láseres en pantalla (`DrawDebugPoints: true`).

### El Colapso de la Sincronización (LockStep)
Al ejecutar la simulación, el dron fue incapaz de despegar. El filtro de estimación de estado (EKF) de PX4 bloqueó los motores arrojando los siguientes errores críticos de seguridad:
* `Preflight Fail: High Accelerometer Bias`
* `Preflight Fail: vertical velocity unstable`

**Análisis de la Causa Raíz:**
El sistema de telemetría de Python reveló saltos temporales de casi **500 milisegundos** entre paquetes. Al invocar la API de AirSim (`getLidarData`) para descargar la densa nube de puntos, el servidor RPC interno de AirSim **pausó el hilo principal del motor de físicas** para empaquetar los datos. 

Esta pausa masiva de medio segundo rompió el `LockStep` (sincronización estricta de reloj entre AirSim y PX4). Para el acelerómetro virtual, el dron se quedó congelado y luego se teletransportó, lo que matemáticamente el EKF interpretó como una fuerza "G" inmensa, resultando en un *High Accelerometer Bias*.

### La Solución y Lección Aprendida
Para permitir el vuelo de prueba, fue necesario reducir drásticamente el perfil del LiDAR (a 4 canales y 10,000 puntos por segundo) y apagar el renderizado en pantalla. Al aligerar la carga de datos, la llamada RPC dejó de estrangular el motor de físicas y el dron pudo volar autónomamente.

**Conclusión Final:** 
Este evento valida tajantemente que **AirSim no es apto para simulaciones LiDAR de alta densidad en tiempo real si se depende del LockStep de PX4**. Para investigaciones avanzadas que involucren nubes de puntos densas (SLAM 3D), la migración a **Gazebo** (Sección 7) es un requerimiento técnico obligatorio, ya que su simulación de sensores está desacoplada del motor principal de físicas y es acelerada por GPU.
