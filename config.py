"""
config.py
---------
Módulo de configuración centralizada. Aquí viven todos los parámetros del
modelo, para que ningún otro módulo tenga "números mágicos" sueltos.
"""

# --- Flujo vehicular (tasas BASE, antes del perfil de hora pico) ---
TASA_BASE = {"N": 0.15, "S": 0.15, "E": 0.10, "O": 0.10}  # veh/seg

# --- Perfil de arribos no homogéneos (hora pico) ---
PICO_INICIO_MIN = 10     # minuto de simulación en que empieza la hora pico
PICO_FIN_MIN = 20
RAMPA_MIN = 3            # minutos de transición antes/después del pico
FACTOR_PICO = 2.2
FACTOR_RAMPA = 1.5
FACTOR_BASE = 1.0

# --- Tiempos del semáforo (segundos) ---
VERDE_NS = 30
VERDE_EO = 25
AMARILLO = 3

# --- Carriles y servicio ---
CAPACIDAD_CARRIL = 1
TIEMPO_CRUCE_MEDIO = 2.0
TIEMPO_CRUCE_DESV = 0.4   # desviación estándar del tiempo de cruce (Normal)

# --- Impacto ecológico ---
CO2_RATE_IDLE = 0.0025    # kg de CO2 por segundo de vehículo detenido/ralentí

# --- Simulación ---
TIEMPO_SIMULACION = 1800  # segundos (30 min)
SEMILLA = 30

# --- Diseño de experimentos (DOE) ---
TIEMPOS_VERDE_NS = [20, 30, 40]
TIEMPOS_VERDE_EO = [15, 25, 35]

DIRECCIONES = ("N", "S", "E", "O")
