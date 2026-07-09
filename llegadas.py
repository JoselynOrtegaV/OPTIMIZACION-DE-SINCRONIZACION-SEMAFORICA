"""
llegadas.py
-----------
Generador de vehículos según un proceso de Poisson NO HOMOGÉNEO, usando
la técnica de "thinning": se generan candidatos con la tasa máxima
(LAMBDA_MAX) y se aceptan con probabilidad lambda(t)/LAMBDA_MAX.
"""

import random
import config as cfg
from vehiculo import proceso_vehiculo


def tasa_llegada(t, direccion):
    """
    Tasa instantánea de llegada lambda(t) [veh/seg] para una dirección,
    en el instante t de la simulación. Simula un perfil de hora pico.
    """
    minuto = t / 60.0
    base = cfg.TASA_BASE[direccion]

    if cfg.PICO_INICIO_MIN <= minuto <= cfg.PICO_FIN_MIN:
        factor = cfg.FACTOR_PICO
    elif (cfg.PICO_INICIO_MIN - cfg.RAMPA_MIN) <= minuto < cfg.PICO_INICIO_MIN or \
         cfg.PICO_FIN_MIN < minuto <= (cfg.PICO_FIN_MIN + cfg.RAMPA_MIN):
        factor = cfg.FACTOR_RAMPA
    else:
        factor = cfg.FACTOR_BASE

    return base * factor


def lambda_max():
    return max(cfg.TASA_BASE.values()) * cfg.FACTOR_PICO


def generador_llegadas(env, direccion, interseccion, semaforo):
    lam_max = lambda_max()
    while True:
        yield env.timeout(random.expovariate(lam_max))
        t = env.now
        lam_t = tasa_llegada(t, direccion)

        if random.random() <= lam_t / lam_max:
            interseccion.registrar_llegada_aceptada(direccion, t)
            env.process(proceso_vehiculo(env, direccion, interseccion, semaforo))

        interseccion.registrar_cola(t, direccion)
