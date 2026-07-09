"""
interseccion.py
---------------
Modela la intersección: cada dirección de acceso es un CARRIL representado
por un simpy.Resource (recurso compartido con cola FIFO). También guarda
la telemetría recolectada durante la simulación.
"""

import simpy
import config as cfg


class Interseccion:
    def __init__(self, env, capacidad_carril=cfg.CAPACIDAD_CARRIL):
        self.env = env
        self.carriles = {
            d: simpy.Resource(env, capacity=capacidad_carril)
            for d in cfg.DIRECCIONES
        }

        # --- Telemetría ---
        self.demoras = []              # demora total por vehículo (seg)
        self.marcas_tiempo = []        # instante de salida de cada vehículo
        self.co2_total = 0.0           # kg de CO2 acumulados (proxy)
        self.serie_colas = []          # (t, direccion, longitud_cola)
        self.tiempos_entre_llegadas = {d: [] for d in cfg.DIRECCIONES}  # para bondad de ajuste
        self.tiempos_cruce = []        # para bondad de ajuste (Normal)
        self._ultima_llegada_aceptada = {d: None for d in cfg.DIRECCIONES}

    def registrar_llegada_aceptada(self, direccion, t):
        """
        Guarda el tiempo entre llegadas aceptadas junto con la marca de
        tiempo (t, dt), para poder filtrar más tarde solo el tramo donde
        la tasa lambda(t) es aproximadamente constante (fuera de la hora
        pico y sus rampas) y así probar bondad de ajuste Exponencial de
        forma correcta sobre un proceso homogéneo por tramos.
        """
        anterior = self._ultima_llegada_aceptada[direccion]
        if anterior is not None:
            self.tiempos_entre_llegadas[direccion].append((t, t - anterior))
        self._ultima_llegada_aceptada[direccion] = t

    def registrar_cola(self, t, direccion):
        cola_actual = len(self.carriles[direccion].queue)
        self.serie_colas.append((t, direccion, cola_actual))

    def registrar_salida(self, t_llegada, t_salida, tiempo_cruce):
        demora = t_salida - t_llegada
        self.demoras.append(demora)
        self.marcas_tiempo.append(t_salida)
        self.tiempos_cruce.append(tiempo_cruce)

        tiempo_detenido = max(0.0, demora - tiempo_cruce)
        self.co2_total += tiempo_detenido * cfg.CO2_RATE_IDLE
