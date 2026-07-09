"""
semaforo.py
-----------
Modela el semáforo como un proceso de eventos discretos CÍCLICO E
INDEPENDIENTE que altera una variable de estado compartida (VERDE/ROJO)
por fase, sin depender de los procesos de vehículos.
"""

import config as cfg


class Semaforo:
    def __init__(self, env, verde_ns=cfg.VERDE_NS, verde_eo=cfg.VERDE_EO,
                 amarillo=cfg.AMARILLO):
        self.env = env
        self.verde_ns = verde_ns
        self.verde_eo = verde_eo
        self.amarillo = amarillo
        self.estado = {"N": "VERDE", "S": "VERDE", "E": "ROJO", "O": "ROJO"}

        # Evento de SimPy que se dispara EXACTAMENTE en el instante en que
        # cambia cualquier fase. Los vehículos se "suscriben" a este evento
        # en vez de sondear el estado periódicamente (polling). Esto es el
        # patrón idiomático de eventos discretos: nadie hace nada hasta que
        # ocurre el evento que le importa.
        self.evento_cambio = env.event()

        self.proceso = env.process(self.ciclo())

    def _cambiar_estado(self, nuevo_estado):
        """Actualiza el estado y notifica a todos los procesos suscritos."""
        self.estado.update(nuevo_estado)
        evento_anterior = self.evento_cambio
        self.evento_cambio = self.env.event()  # nuevo evento para el próximo cambio
        evento_anterior.succeed()              # dispara el evento anterior (despierta a los que esperaban)

    def ciclo(self):
        """Alterna infinitamente entre las fases NS y EO."""
        while True:
            # Fase Norte-Sur en verde
            self._cambiar_estado({"N": "VERDE", "S": "VERDE", "E": "ROJO", "O": "ROJO"})
            yield self.env.timeout(self.verde_ns)

            # Amarillo: despeje de la intersección
            self._cambiar_estado({"N": "ROJO", "S": "ROJO"})
            yield self.env.timeout(self.amarillo)

            # Fase Este-Oeste en verde
            self._cambiar_estado({"E": "VERDE", "O": "VERDE", "N": "ROJO", "S": "ROJO"})
            yield self.env.timeout(self.verde_eo)

            self._cambiar_estado({"E": "ROJO", "O": "ROJO"})
            yield self.env.timeout(self.amarillo)

    def en_verde(self, direccion):
        return self.estado[direccion] == "VERDE"
