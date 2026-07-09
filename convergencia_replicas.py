"""
convergencia_replicas.py
------------------------
Genera la Figura 6 del reporte: muestra cómo se reduce el margen de
error relativo del intervalo de confianza al 95% a medida que aumenta
el número de réplicas (n), usando la fórmula iterativa de Law (2015)
basada en la distribución t de Student:

    E(n) = t_(0.975, n-1) * s / sqrt(n)

Usa como insumo la media y desviación estándar del piloto de 15
réplicas ya calculado en analisis.py (numero_optimo_replicas), por lo
que no vuelve a correr la simulación: es un cálculo analítico sobre
esos dos números.

Uso:
    python convergencia_replicas.py
"""

import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

# Media y desviación estándar del piloto de 15 réplicas
# (obtenidas de analisis.py -> numero_optimo_replicas())
XBAR_PILOTO = 57.11873144422288
S_PILOTO = 13.148689788912977

N_USADO_DOE = 10
N_REQUERIDO = 98
PRECISION_OBJETIVO = 0.05  # 5%


def calcular_precision_relativa(xbar=XBAR_PILOTO, s=S_PILOTO, n_max=150):
    """
    Calcula, para cada n entre 2 y n_max, el margen de error relativo
    (como % de la media) que tendría el intervalo de confianza al 95%
    si se hubieran corrido n réplicas con esa media y desviación
    estándar piloto.
    """
    ns = np.arange(2, n_max)
    E_rel = []
    for n in ns:
        t_val = stats.t.ppf(0.975, df=n - 1)
        E = t_val * s / np.sqrt(n)
        E_rel.append(100 * E / xbar)
    return ns, np.array(E_rel)


def graficar_convergencia(ruta="outputs/convergencia_replicas.png"):
    ns, E_rel = calcular_precision_relativa()

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(ns, E_rel, color="steelblue", lw=2)
    ax.axhline(100 * PRECISION_OBJETIVO, color="crimson", linestyle="--",
               label=f"Precisión objetivo ({int(PRECISION_OBJETIVO*100)}%)")
    ax.axvline(N_USADO_DOE, color="darkorange", linestyle=":",
               label=f"n={N_USADO_DOE} (usado en el DOE)")
    ax.axvline(N_REQUERIDO, color="seagreen", linestyle=":",
               label=f"n={N_REQUERIDO} (requerido para {int(PRECISION_OBJETIVO*100)}%)")

    ax.set_xlabel("Número de réplicas (n)")
    ax.set_ylabel("Precisión relativa del IC 95% (% de la media)")
    ax.set_title("Convergencia de la Precisión del Intervalo de Confianza vs. Número de Réplicas")
    ax.legend()
    ax.set_ylim(0, 40)
    fig.tight_layout()
    fig.savefig(ruta, dpi=120)
    return fig


if __name__ == "__main__":
    graficar_convergencia()
    print("Gráfica guardada en outputs/convergencia_replicas.png")
