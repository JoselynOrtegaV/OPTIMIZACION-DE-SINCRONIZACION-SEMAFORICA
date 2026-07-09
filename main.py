"""
main.py
-------
Punto de entrada del proyecto. Ejecuta, en orden:
  1) Una corrida individual del MOTOR DE EVENTOS DISCRETOS con los
     parámetros por defecto (config.py) y grafica sus resultados.
  2) El ANÁLISIS DE BONDAD DE AJUSTE de los supuestos estocásticos
     (llegadas ~ Exponencial, tiempos de cruce ~ Normal).
  3) El DISEÑO DE EXPERIMENTOS (DOE) comparando distintas combinaciones
     de tiempos de semáforo.

Uso:
    python main.py
"""

import os
import numpy as np

import config as cfg
from motor_eventos import ejecutar_motor
from visualizacion import graficar_demora, graficar_colas
from bondad_ajuste import reporte_bondad_ajuste
from experimento_doe import correr_experimento, guardar_csv, graficar_doe, imprimir_tabla


def main():
    os.makedirs("outputs", exist_ok=True)

    # ------------------------------------------------------------------
    # 1) Corrida individual del motor de eventos discretos
    # ------------------------------------------------------------------
    print("=" * 60)
    print("CORRIDA INDIVIDUAL DEL MOTOR DE EVENTOS DISCRETOS")
    print("=" * 60)
    interseccion = ejecutar_motor()

    demora_media = np.mean(interseccion.demoras)
    print(f"Vehículos procesados: {len(interseccion.demoras)}")
    print(f"Demora promedio: {demora_media:.2f} s")
    print(f"Demora máxima: {np.max(interseccion.demoras):.2f} s")
    print(f"CO2 total estimado: {interseccion.co2_total:.3f} kg")

    graficar_demora(interseccion)
    graficar_colas(interseccion)
    print("Gráficas guardadas en outputs/")

    # ------------------------------------------------------------------
    # 2) Bondad de ajuste
    # ------------------------------------------------------------------
    print()
    reporte_bondad_ajuste(interseccion, direccion_llegadas="E")

    # ------------------------------------------------------------------
    # 3) Diseño de experimentos (DOE)
    # ------------------------------------------------------------------
    print()
    print("=" * 60)
    print("DISEÑO DE EXPERIMENTOS (DOE)")
    print("=" * 60)
    resultados = correr_experimento(n_replicas=10)
    imprimir_tabla(resultados)
    guardar_csv(resultados)
    graficar_doe(resultados)
    print("")


if __name__ == "__main__":
    main()
