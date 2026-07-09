# Simulación del Flujo Vehicular en una Intersección

Proyecto modularizado de simulación de eventos discretos (DES) para el
diseño óptimo de tiempos de semáforo en una intersección de alta
congestión, usando `SimPy`.

## Estructura del proyecto

```
proyecto_semaforo/
├── config.py            # Todos los parámetros del modelo en un solo lugar
├── semaforo.py           # Proceso semafórico cíclico e independiente (VERDE/ROJO)
├── interseccion.py       # Carriles como recursos compartidos + telemetría
├── vehiculo.py           # Ciclo de vida de un vehículo (proceso de evento)
├── llegadas.py           # Generador de llegadas NO homogéneas (thinning)
├── motor_eventos.py      # MOTOR DE EVENTOS DISCRETOS: arma y corre la simulación
├── bondad_ajuste.py      # Pruebas de bondad de ajuste (KS y Chi-cuadrado)
├── experimento_doe.py    # Diseño de experimentos: compara tiempos de semáforo
├── visualizacion.py      # Gráficas de una corrida individual
├── main.py               # Punto de entrada: corre todo en orden
└── outputs/              # Gráficas (.png) y resultados (.csv) generados
```

## Cómo correrlo

```bash
pip install simpy numpy scipy matplotlib
python main.py
```

Esto ejecuta, en orden:

1. **Motor de eventos discretos** (`motor_eventos.py`): una corrida
   individual con los parámetros por defecto de `config.py`, y guarda
   gráficas de la demora en el tiempo y la longitud de cola por
   dirección en `outputs/`.
2. **Bondad de ajuste** (`bondad_ajuste.py`): valida que los tiempos
   entre llegadas (en el tramo de tasa constante, fuera de la hora
   pico) se ajustan a una distribución **Exponencial**, y que los
   tiempos de cruce se ajustan a una distribución **Normal**, usando
   las pruebas de **Kolmogorov-Smirnov** y **Chi-cuadrado**.
3. **Diseño de experimentos (DOE)** (`experimento_doe.py`): corre el
   motor con 9 combinaciones de tiempos de semáforo (Verde NS × Verde
   EO) y reporta cuál minimiza la demora promedio y las emisiones de
   CO2 (proxy).

## Notas sobre la bondad de ajuste

- La prueba **Kolmogorov-Smirnov (KS)** es la más adecuada para datos
  continuos y tamaños de muestra moderados: no depende de cómo se
  agrupen los datos en bins.
- La prueba **Chi-cuadrado** es más sensible al número de bins y al
  tamaño de muestra (necesita frecuencias esperadas >= 5 por bin para
  ser confiable), por lo que puede rechazar el ajuste incluso cuando
  KS no lo hace, especialmente con muestras pequeñas. Ambas pruebas se
  reportan por transparencia metodológica, pero KS es el criterio
  principal.

## Metodología

Este es un modelo de **Simulación de Eventos Discretos (DES)**: el
estado del sistema (colas, fase del semáforo) cambia únicamente en
instantes puntuales (llegada de un vehículo, inicio/fin de cruce,
cambio de fase), no de forma continua. La aleatoriedad se incorpora
**dentro** de ese marco de eventos discretos mediante variables
estocásticas (llegadas tipo Poisson no homogéneo vía *thinning*, y
tiempos de cruce ~ Normal), por lo que el modelo es, en conjunto, una
simulación de eventos discretos y estocástica.
