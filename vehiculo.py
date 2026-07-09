"""
vehiculo.py
-----------
Ciclo de vida de un vehículo dentro del motor de eventos discretos:
llega, hace fila en su carril, espera a que el semáforo esté en VERDE,
y cruza la intersección.
"""

import random
import config as cfg


def proceso_vehiculo(env, direccion, interseccion, semaforo):
    t_llegada = env.now
    carril = interseccion.carriles[direccion]

    with carril.request() as turno:
        yield turno  # 1. Espera su posición en la fila del carril (recurso compartido)

        # 2. Espera a que el semáforo de su dirección esté en VERDE.
        #    Enfoque puramente basado en EVENTOS (no sondeo/polling): el
        #    proceso se "suscribe" al evento de cambio del semáforo y solo
        #    se reactiva exactamente cuando ese evento ocurre.
        while not semaforo.en_verde(direccion):
            yield semaforo.evento_cambio

        # 3. Cruza la intersección (tiempo estocástico ~ Normal)
        tiempo_cruce = max(0.5, random.normalvariate(
            cfg.TIEMPO_CRUCE_MEDIO, cfg.TIEMPO_CRUCE_DESV))
        yield env.timeout(tiempo_cruce)

    t_salida = env.now
    interseccion.registrar_salida(t_llegada, t_salida, tiempo_cruce)
