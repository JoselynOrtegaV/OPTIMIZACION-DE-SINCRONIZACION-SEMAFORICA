"""
motor_eventos.py
----------------
MOTOR DE EVENTOS DISCRETOS del modelo. Este módulo es el responsable de:
  1) Crear el entorno de simulación (el "reloj" de eventos, simpy.Environment).
  2) Instanciar el semáforo, la intersección y los generadores de llegada.
  3) Avanzar la simulación evento por evento (env.run) hasta el tiempo final.
  4) Devolver la telemetría recolectada para su posterior análisis.

Es el único módulo que sabe "cómo" se ejecuta la simulación; el resto de
módulos (semaforo, interseccion, vehiculo, llegadas) solo describen el
comportamiento de cada componente, sin preocuparse por el motor en sí.
Esto es lo que en la literatura de simulación se llama el "DES engine":
el planificador de eventos que decide qué proceso corre y cuándo.
"""

import random
import simpy

import config as cfg
from semaforo import Semaforo
from interseccion import Interseccion
from llegadas import generador_llegadas


def ejecutar_motor(verde_ns=cfg.VERDE_NS, verde_eo=cfg.VERDE_EO,
                    tiempo_simulacion=cfg.TIEMPO_SIMULACION, semilla=cfg.SEMILLA):
    """
    Arranca y corre el motor de eventos discretos con los parámetros dados.
    Devuelve el objeto `Interseccion` con toda la telemetría recolectada,
    lista para pasarla a los módulos de análisis (bondad de ajuste, DOE, etc).
    """
    random.seed(semilla)

    env = simpy.Environment()                       # 1. Reloj de eventos
    semaforo = Semaforo(env, verde_ns, verde_eo)      # 2. Proceso semafórico
    interseccion = Interseccion(env, cfg.CAPACIDAD_CARRIL)

    # 3. Un generador de llegadas independiente por cada dirección
    for direccion in cfg.DIRECCIONES:
        env.process(generador_llegadas(env, direccion, interseccion, semaforo))

    # 4. Avanza el reloj de evento en evento hasta tiempo_simulacion
    env.run(until=tiempo_simulacion)

    return interseccion


if __name__ == "__main__":
    resultado = ejecutar_motor()
    print(f"Vehículos procesados: {len(resultado.demoras)}")
