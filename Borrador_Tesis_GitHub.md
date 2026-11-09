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

A continuación, se analizan las tres opciones líderes en el mercado actual para integraciones de investigación y rescate:

## 3.1 Velodyne Puck LITE (VLP-16)
Históricamente, Velodyne ha sido el estándar de oro en robótica móvil e investigación astronómica/automotriz.
- **Peso:** ~590 gramos (la versión LITE está optimizada para drones, a diferencia del Puck estándar de 830g).
- **Patrón de Escaneo:** Mecánico rotativo (360° Horizontal x 30° Vertical).
- **Costo:** ~$4,000 USD (difícil de conseguir nuevo ya que Velodyne fue absorbida por Ouster; el mercado de segunda mano ronda los $1,500 - $2,000 USD).
- **Veredicto para FAST-LIO2:** Funciona bien, pero su patrón de escaneo repetitivo clásico de 16 líneas no aprovecha al máximo la estructura *ikd-Tree* de FAST-LIO2. Además, su peso sigue siendo alto para micro-drones ágiles.

## 3.2 Ouster OS0
Ouster revolucionó el mercado con sus sensores de estado sólido digital y altísima resolución. El OS0 está diseñado con un campo de visión ultra-amplio.
- **Peso:** ~445 gramos.
- **Patrón de Escaneo:** Digital rotativo (360° Horizontal x 90° Vertical). El altísimo FoV vertical es excelente para drones porque "ven" tanto el techo como el suelo en túneles.
- **Costo:** ~$6,000+ USD.
- **Veredicto para FAST-LIO2:** Es una maravilla técnica, pero su alto costo lo hace restrictivo para muchos presupuestos universitarios o de validación de concepto (PoC).

## 3.3 Livox Mid-360 (La Revolución de DJI)
Livox, una filial impulsada por DJI, cambió por completo las reglas del juego al abandonar el giro mecánico tradicional e introducir prismas giratorios que generan un **patrón de escaneo de roseta (no repetitivo)**.
- **Peso:** Increíbles **265 gramos**.
- **Patrón de Escaneo:** No repetitivo (360° Horizontal x 59° Vertical). Al no repetir la línea láser, a medida que pasa el tiempo (fracciones de segundo), el sensor "pinta" todo el entorno de forma mucho más densa que un LiDAR de 16 o 32 líneas tradicional.
- **Costo:** ~$1,000 - $1,200 USD.
- **Veredicto para FAST-LIO2:** **Excepcional.** El algoritmo FAST-LIO2 fue *literalmente* diseñado y optimizado originalmente por el equipo de la Universidad de Hong Kong (HKU) utilizando sensores Livox (como el Avia y el Mid-360). La matemática del IEKF en FAST-LIO2 está hecha a medida para procesar nubes de puntos densas no repetitivas.

> [!TIP]
> **El Patrón No Repetitivo y FAST-LIO2**
> Mientras un Velodyne siempre escanea las mismas 16 líneas horizontales dejando "huecos" vacíos en la geometría de un pasillo liso, el Livox Mid-360 dibuja flores matemáticas que cubren casi el 100% de la superficie en un segundo. Esto le da a FAST-LIO2 muchísimas más características únicas (esquinas, bordes) para agarrarse y no perderse en la oscuridad.

---

## 3.4 Conclusión y Selección de Hardware para el Proyecto

Basado en la investigación previa, la recomendación técnica innegable para este proyecto es el **Livox Mid-360**. 

**Justificación para la tesis:**
1. **Sinergia Algorítmica:** FAST-LIO2 y Livox Mid-360 son actualmente el estado del arte indiscutido en micro-UAVs. El algoritmo extrae el máximo potencial de este hardware.
2. **Capacidad de Carga (Payload):** Sus 265g permiten que casi cualquier dron quadcopter estándar (como un dron ensamblado sobre un marco F450 con PX4) pueda levantarlo junto con una computadora compañera (Raspberry Pi 4 o Jetson Nano) sin comprometer drásticamente la batería.
3. **Viabilidad Económica:** Su costo (una fracción del precio de un Ouster o Velodyne) permite que la investigación escale rápidamente de la simulación en AirSim a un prototipo físico.

> [!IMPORTANT]
> **Siguiente paso lógico:** Demostrar que en nuestra simulación (el gemelo digital en AirSim con el dron actualizado) podemos simular el comportamiento de este sensor específico (inyectando ruido y ajustando el FoV a 360x59) para validar la cadena de procesamiento de datos antes de hacer la compra.
