"""
visualizacion.py
----------------
Gráficos de una corrida individual del motor de eventos discretos:
evolución de la demora en el tiempo y longitud de cola por dirección.
"""

import numpy as np
import matplotlib.pyplot as plt

import config as cfg


def graficar_demora(interseccion, ruta="outputs/demora_en_el_tiempo.png"):
    demora_media = np.mean(interseccion.demoras)

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.scatter(interseccion.marcas_tiempo, interseccion.demoras, alpha=0.6, color="royalblue")
    ax.axhline(y=demora_media, color="crimson", linestyle="--",
               label=f"Demora Promedio: {demora_media:.1f} s")
    ax.set_title("Evolución de la Demora de Viaje en el Tiempo")
    ax.set_xlabel("Tiempo de Simulación (segundos)")
    ax.set_ylabel("Demora Total End-to-End (s)")
    ax.legend()
    fig.tight_layout()
    fig.savefig(ruta, dpi=120)
    return fig


def graficar_colas(interseccion, ruta="outputs/colas_por_direccion.png"):
    fig, ax = plt.subplots(figsize=(9, 4.5))
    colores = {"N": "royalblue", "S": "seagreen", "E": "darkorange", "O": "purple"}

    for direccion in cfg.DIRECCIONES:
        puntos = [(t, c) for (t, d, c) in interseccion.serie_colas if d == direccion]
        if puntos:
            tiempos, colas = zip(*puntos)
            ax.plot(tiempos, colas, label=f"Dirección {direccion}", color=colores[direccion], alpha=0.8)

    ax.set_title("Longitud de Cola por Dirección a lo Largo del Tiempo")
    ax.set_xlabel("Tiempo de Simulación (segundos)")
    ax.set_ylabel("Vehículos en Cola")
    ax.legend()
    fig.tight_layout()
    fig.savefig(ruta, dpi=120)
    return fig
