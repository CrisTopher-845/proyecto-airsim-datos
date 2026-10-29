# Mapeo Autónomo y SLAM 3D en Tiempo Real con LiDAR

## Capítulo 1: Introducción y Estado del Arte

### 1.1 Contexto y Motivación: Respuesta a Desastres Naturales
En la estela de desastres naturales catastróficos—tales como el reciente y trágico deslizamiento de tierra en Filipinas, así como terremotos y socavones urbanos—la respuesta rápida y segura es el factor más crítico para salvar vidas. Los métodos topográficos y de rescate tradicionales son inherentemente lentos y exponen a los rescatistas a réplicas o colapsos estructurales. 

La integración de **Vehículos Aéreos No Tripulados (UAVs)** equipados con sensores **LiDAR (Light Detection and Ranging)** ha emergido como una herramienta transformadora. A diferencia de las cámaras ópticas (fotogrametría), el LiDAR utiliza pulsos láser que pueden penetrar humo, polvo y vegetación densa, revelando la topografía real y la integridad de las estructuras colapsadas, independientemente de las condiciones de iluminación.

### 1.2 El Problema de los Entornos "GPS-Denied"
El mayor desafío técnico en zonas de desastre es la pérdida de la infraestructura de comunicaciones y la degradación de la señal GPS. Los drones comerciales dependen casi exclusivamente del GPS para mantener su posición. Cuando un dron ingresa a un edificio colapsado, un cañón profundo o una zona subterránea, la pérdida de señal resulta en derivas críticas y colisiones.

Para resolver esto, la robótica moderna utiliza **SLAM (Simultaneous Localization and Mapping)**. Esta técnica matemática permite a un robot construir un mapa de un entorno desconocido mientras simultáneamente estima su propia posición dentro de ese mapa, logrando una navegación puramente autónoma.

### 1.3 Referente Industrial: Exyn Technologies y el Nivel de Autonomía 4 (AL4)
Para establecer un estándar de investigación, se toma como referencia el sistema **Nexys** desarrollado por *Exyn Technologies*. Este módulo representa el estado del arte en exploración autónoma:
- **Autonomía AL4:** Capacidad de navegar sin piloto humano y sin mapas previos en entornos 100% oscuros y sin GPS (minas subterráneas, edificios en ruinas).
- **Independencia de Plataforma:** El algoritmo de SLAM y control es agnóstico al hardware; puede montarse en un dron o llevarse en la mano.
- **Mapeo en Tiempo Real:** Procesa hasta 1.92 millones de puntos por segundo localmente (Edge Computing), permitiendo a los rescatistas ver el mapa 3D en una tablet mientras el dron aún está volando en la zona de peligro.

Este nivel de autonomía e independencia de la nube (Cloud) es el objetivo final de la arquitectura que se propone investigar.

---

## Capítulo 2: Marco Teórico y Algoritmos de SLAM LiDAR

Para lograr la autonomía de sistemas como Exyn Nexys, es fundamental entender y dominar la evolución de las matemáticas detrás de los algoritmos SLAM LiDAR. El cálculo en tiempo real de nubes de puntos densas a bordo de un dron requiere optimizaciones extremas.

### 2.1 LOAM (LiDAR Odometry and Mapping)
Desarrollado en 2014, LOAM es el abuelo de los algoritmos modernos. 
- **Matemática:** Separa el problema complejo de SLAM en dos algoritmos simultáneos de menor complejidad. Un hilo corre a alta frecuencia estimando la odometría basándose en la extracción de características (bordes y planos), mientras un segundo hilo mapea y refina la nube de puntos a baja frecuencia.
- **Limitación en Desastres:** LOAM depende puramente del láser. En escenarios donde hay polvo denso, espacios sin características geométricas claras (un pasillo largo y liso) o movimientos bruscos del dron por el viento, el algoritmo pierde su estimación (falla catastrófica).

### 2.2 LIO-SAM (Tightly-coupled LiDAR Inertial Odometry via Smoothing and Mapping)
Para solucionar la debilidad de LOAM, la industria se movió a LIO-SAM, el cual introduce la **Fusión de Sensores (Sensor Fusion)**.
- **Matemática (Factor Graphs):** LIO-SAM acopla "estrechamente" las lecturas del LiDAR con la IMU (Unidad de Medición Inercial) utilizando una estructura matemática llamada *Factor Graph* (Grafo de Factores).
- **Ventaja Principal:** Realiza un "Loop Closure" (Cierre de bucle) global. Si el dron vuelve a pasar por una zona en ruinas que ya visitó, el grafo de factores corrige matemáticamente toda la deriva (drift) acumulada en el mapa, entregando nubes de puntos de precisión centimétrica.
- **Desafío:** Es computacionalmente pesado a medida que el mapa crece, lo cual es difícil de procesar en la computadora de a bordo del dron.

### 2.3 FAST-LIO2 (Fast LiDAR-Inertial Odometry) - El Estado del Arte
Si LIO-SAM busca el mapa perfecto, FAST-LIO2 busca la velocidad extrema requerida por drones ágiles.
- **Matemática (IEKF y ikd-Tree):** En lugar de usar grafos pesados, FAST-LIO utiliza un Filtro de Kalman Extendido Iterativo (IEKF). La gran revolución matemática de FAST-LIO2 es la introducción del *ikd-Tree* (Árbol k-d incremental). Esta estructura de datos dinámica permite actualizar, buscar e insertar puntos en el mapa en tiempos de microsegundos, sin importar el tamaño del mapa.
- **Por qué es ideal para el proyecto:** Su asombrosa eficiencia computacional permite procesar el SLAM en tiempo real en microcomputadoras (como una Raspberry Pi o Jetson Nano) consumiendo una fracción de la CPU, dejándole recursos al dron para la planificación de evasión de obstáculos.

### 2.4 Resumen de Dirección de Investigación
La tesis se centrará en analizar e implementar la familia de algoritmos basados en LIO (LiDAR-Inertial Odometry), utilizando como base matemática el Filtro de Kalman o Grafos de Factores, probándolos primero en el gemelo digital de **AirSim + PX4** antes de cualquier transición a hardware de rescate.

---

# Capítulo 3: Evaluación y Selección de Hardware LiDAR

Tras haber establecido que la familia de algoritmos LIO (específicamente **FAST-LIO2**) es la opción matemática más robusta para procesar SLAM en tiempo real a bordo de un dron, el siguiente paso es seleccionar el hardware físico (sensor LiDAR) que alimentará de datos al sistema.

Para aplicaciones en UAVs (Vehículos Aéreos No Tripulados), la selección del hardware es un compromiso estricto entre **peso, costo, campo de visión (FoV) y patrón de escaneo**.

A continuación, se analizan las opciones líderes en el mercado actual para integraciones de investigación y rescate:

## 3.1 Velodyne Puck LITE (VLP-16)
Históricamente, Velodyne ha sido el estándar de oro en robótica móvil.
- **Peso:** ~590 gramos (optimizado para drones).
- **Patrón de Escaneo:** Mecánico rotativo (360° Horizontal x 30° Vertical).
- **Costo:** ~$4,000 USD.
- **Veredicto para FAST-LIO2:** Funciona bien, pero su patrón de escaneo repetitivo clásico de 16 líneas no aprovecha al máximo la estructura *ikd-Tree* de FAST-LIO2.

## 3.2 Ouster OS0
Ouster revolucionó el mercado con sus sensores de estado sólido digital.
- **Peso:** ~445 gramos.
- **Patrón de Escaneo:** Digital rotativo (360° Horizontal x 90° Vertical).
- **Costo:** ~$6,000+ USD.
- **Veredicto para FAST-LIO2:** Maravilla técnica, pero su alto costo lo hace restrictivo para validación de concepto (PoC).

## 3.3 Livox Mid-360 (La Revolución de DJI)
Livox introdujo prismas giratorios que generan un **patrón de escaneo de roseta (no repetitivo)**.
- **Peso:** Increíbles **265 gramos**.
- **Patrón de Escaneo:** No repetitivo (360° Horizontal x 59° Vertical). Al no repetir la línea láser, "pinta" todo el entorno de forma mucho más densa en fracciones de segundo.
- **Costo:** ~$1,000 - $1,200 USD.
- **Veredicto para FAST-LIO2:** **Excepcional.** El algoritmo FAST-LIO2 fue optimizado originalmente por la Universidad de Hong Kong (HKU) utilizando este mismo sensor.

> [!TIP]
> **El Patrón No Repetitivo y FAST-LIO2**
> Mientras un Velodyne escanea las mismas 16 líneas horizontales dejando huecos en pasillos lisos, el Livox Mid-360 dibuja flores matemáticas que cubren casi el 100% de la superficie, dándole a FAST-LIO2 muchísimas características únicas para no perderse en la oscuridad.

---

## 3.4 Conclusión y Selección de Hardware para el Proyecto

La recomendación técnica innegable para este proyecto es el **Livox Mid-360**. 
1. **Sinergia Algorítmica:** FAST-LIO2 y Livox Mid-360 extraen el máximo potencial mutuo.
2. **Capacidad de Carga (Payload):** Sus 265g permiten montarlo en un quadcopter F450 con PX4 junto a una Companion Computer (Raspberry Pi/Jetson Nano) sin comprometer la batería.
3. **Viabilidad Económica:** Costo fraccionario ideal para escalar de simulación a prototipo.

---

## 3.5 Validación del Sensor Livox Mid-360 en el Gemelo Digital (AirSim)

Como paso previo a la adquisición física, se emuló el comportamiento del sensor en el simulador fotorealista AirSim. En esta fase, se evidenciaron limitaciones arquitectónicas clave del motor de simulación.

### 3.5.1 Parametrización del LiDAR Virtual
Inicialmente, se intentó igualar la capacidad masiva del sensor físico configurando `200,000 puntos/s` y `16 canales` en `settings.json`. Sin embargo, esto generó un colapso en la simulación. Tras extensas pruebas empíricas, se determinó una **parametrización estable y balanceada** para no asfixiar el procesador (CPU) de la máquina anfitriona:
- **Tasa de muestreo (PointsPerSecond):** 30,000 puntos/s.
- **Canales (NumberOfChannels):** 8 canales.
- **Frecuencia de actualización (RotationsPerSecond):** 10 Hz.
- **Campo de visión (FOV):** Horizontal de 360°, operando sin restricción vertical artificial para maximizar el abanico cónico hacia el suelo.

### 3.5.2 Caso de Estudio y Resolución de Problemas de Simulación
Durante la integración, se descubrieron y resolvieron tres problemas críticos inherentes a la simulación de sensores de alta densidad:

1. **El Cuello de Botella RPC y Ruptura de Sincronización (LockStep):** 
   Al intentar extraer 100,000 o 200,000 puntos por segundo de AirSim hacia Python mediante la API (getLidarData), el servidor interno RPC (Remote Procedure Call) pausaba el hilo principal del motor de físicas durante casi 500 milisegundos para empaquetar los datos. Esta pausa masiva rompía la sincronización de reloj estricta (LockStep) entre AirSim y el controlador PX4 SITL. Para el acelerómetro virtual, el dron parecía congelarse y teletransportarse, lo que el estimador EKF interpretaba como una fuerza "G" inmensa, arrojando errores letales (`Preflight Fail: High Accelerometer Bias`) que impedían el despegue. La reducción de la carga a **30,000 puntos/s** alivianó el cuello de botella, permitiendo recuperar la sincronización y habilitar el vuelo.
2. **Saturación Gráfica:** El motor Unreal Engine sufría enormes caídas de fotogramas al renderizar visualmente los puntos láser. Se solucionó deshabilitando el renderizado de depuración (`DrawDebugPoints: false`).
3. **Auto-Oclusión por el Chasis:** El sensor detectaba los brazos del propio dron virtual. Se corrigió elevando el marco de referencia del LiDAR medio metro sobre el dron (`Z = -0.5m`).

### 3.5.3 Resultados de la Validación
Bajo los parámetros estabilizados, el script en Python demostró capturar nubes de puntos de manera constante, generando formatos geométricos (`.ply`) que fueron visualizados en **CloudCompare**, evidenciando patrones de escaneo de alta resolución del suelo y las estructuras verticales, habilitando el sistema para SLAM.

---

## 3.6 Optimización de Trayectorias Autónomas para Mapeo 3D (Overscan)

Diseñar una ruta autónoma para escanear un entorno urbano denso (el escenario "Blocks") y generar una nube de puntos sin áreas ocluidas requirió optimizaciones específicas para compensar las limitaciones del dron virtual.

### 3.6.1 Identificación de Problemas en Rutas Tradicionales
Ensayos iniciales con cuadrículas densas (step de 5 a 10 metros) revelaron tres fallos:
1. **Limitación Energética (Battery Failsafe):** Rutas muy largas drenaban la batería simulada, provocando abortos de emergencia (RTL) y colisiones durante el aterrizaje a ciegas (`blind land`).
2. **Colisión con Entorno:** La altitud estándar (-30m) causaba impactos con los rascacielos.
3. **Oclusión de Caras Exteriores (Sombras):** Al delimitar la ruta al ras de la ciudad (200x200m), el dron no lograba observar las paredes externas de los bloques ubicados en los bordes.

### 3.6.2 Solución Implementada: Patrón Cross-Hatch de Alta Eficiencia y Overscan
Se rediseñó el algoritmo (`mision_autonoma.py`) implementando un patrón de **Doble Cuadrícula (Cross-Hatch) con Overscan**:
- **Altitud de -60 metros:** Franquea todos los obstáculos y maximiza la huella del láser en el suelo.
- **Overscan (260x260m):** El área de vuelo se amplió 30 metros más allá de los edificios. Volar por fuera del perímetro permitió al LiDAR de 360° escanear las caras posteriores de los bloques periféricos antes de dar la vuelta.
- **Paso (Step) de 40 metros:** La gran altura permitió separar las líneas de vuelo a 40 metros, manteniendo solapamiento y reduciendo drásticamente el tiempo de vuelo para evitar el failsafe por batería.
- **Guiñada Dinámica (Yaw):** Orientación continua (`math.atan2`) en la dirección de avance.

### 3.6.3 Reconstrucción de Superficie en MeshLab
Para transformar los puntos en un modelo 3D sólido (Watertight Mesh):
1. **Cálculo de Normales:** Orientación de puntos determinando su normal (`Compute normals for point sets`).
2. **Screened Poisson:** Generación de la malla poligonal con algoritmo de Poisson (Depth = 10).
3. **Limpieza de Geometría:** Aplicación de filtros de limpieza (`Pre-Clean`) para erradicar errores de normales nulas, eliminando también la burbuja exterior sobrante. El gemelo digital 3D resultante fue un éxito absoluto.

---

# Capítulo 4: Arquitectura de Integración y Escalabilidad Futura

Con el LiDAR validado conceptualmente y las mecánicas de vuelo autónomo optimizadas, es imperativo establecer un marco arquitectónico escalable. Un LiDAR físico moderno genera millones de puntos por segundo, un volumen de datos que un script en Python ejecutado en bucle simple es incapaz de procesar sin colapsar.

## 4.1 El Rol de ROS 2 como Middleware
Para evitar cuellos de botella en el procesamiento, la arquitectura debe migrar a **ROS 2 (Robot Operating System)**. ROS 2 actúa como middleware descentralizado:
- **El Dron (PX4):** Administra exclusivamente la estabilidad, waypoints y sensores inerciales.
- **El Sensor (LiDAR):** Publica la nube de puntos cruda (`sensor_msgs/PointCloud2`).
- **El Cerebro (ROS 2):** Absorbe los datos masivos mediante nodos especializados en C++, los procesa a través de filtros espaciales (Voxel Grids) y algoritmos de SLAM (FAST-LIO2 u OctoMap), y le devuelve a PX4 instrucciones instantáneas para evasión de obstáculos dinámicos.

La adopción actual de contenedores Docker agnósticos prepara el terreno perfectamente para esta transición.

## 4.2 Debate Arquitectónico de Simulación: AirSim vs Gazebo
Como demostró el caso de estudio del Cuello de Botella RPC (Sección 3.5.2), forzar simulaciones de LiDAR densos en motores no especializados destruye la integridad del controlador de vuelo (LockStep).

| Ámbito de Análisis | Módulo AirSim (Unreal Engine) | Módulo Gazebo (Harmonic / Classic) |
| :--- | :--- | :--- |
| **Fidelidad Visual (Cámaras)** | **Ganador.** Entornos fotorrealistas ideales para IA y Visión Computacional. | Básica. Geometrías simples y texturas planas. |
| **Computación LiDAR** | Altamente pesada (Basada en CPU). Propenso a romper sincronización. | **Ganador.** Aceleración total por GPU. Simula LiDARs de 128 canales fluidamente. |
| **Conectividad con ROS 2** | Requiere wrappers y scripts intermedios pesados. | **Nativo.** Publica mensajes estandarizados directos. Modelos PX4 SITL incluidos. |

**Conclusión técnica:** AirSim es excelente para validación lógica y de visión computacional. Sin embargo, para escalar a simulaciones de SLAM 3D y nubes de puntos de alta densidad en tiempo real, la migración a Gazebo es un requerimiento obligatorio debido a su aceleración por hardware dedicada.

## 4.3 Hoja de Ruta (Roadmap)
La viabilidad del proyecto está demostrada. La expansión se regirá por la siguiente estructura evolutiva:

- **Fase 1 (Actual - AirSim & Python):** Uso de un LiDAR virtual optimizado (8 canales, 30kHz) para validación algorítmica de trayectorias (Cross-Hatch, Overscan) y extracción en crudo para procesamiento topográfico offline (MeshLab).
- **Fase 2 (Software - Integración ROS 2):** Desplegar contenedores de ROS 2 paralelos. Delegar a ROS 2 el filtrado masivo de nubes de puntos y la ejecución de FAST-LIO2, migrando el entorno de pruebas a Gazebo para garantizar la estabilidad del LockStep bajo cargas extremas.
- **Fase 3 (Hardware Físico):** Adquisición del Livox Mid-360. Ensamblaje en un UAV comercial (ej. F450 con Pixhawk) equipado con una *Companion Computer* (Jetson Nano). Debido al diseño agnóstico basado en ROS 2 y MAVLink, el código físico será idéntico al código simulado, cerrando el ciclo de investigación robótica.
