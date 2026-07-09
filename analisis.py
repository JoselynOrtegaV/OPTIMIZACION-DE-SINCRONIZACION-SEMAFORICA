"""
analisis.py
-----------
Análisis estadístico complementario al DOE:
  1) Número óptimo de réplicas (piloto + fórmula iterativa de Law, 2015).
  2) Simulación Monte Carlo para propagación de incertidumbre paramétrica.
  3) Análisis de sensibilidad (one-at-a-time, +/-20%) sobre variables críticas.

Todo se evalúa sobre el escenario óptimo encontrado en el DOE
(VERDE_NS = 40 s, VERDE_EO = 25 s). Genera gráficas en outputs/ y un
reporte en consola, igual que bondad_ajuste.py y experimento_doe.py.

Uso:
    python analisis.py
"""

import copy
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

import config as cfg
from motor_eventos import ejecutar_motor

VERDE_NS_OPT = 40
VERDE_EO_OPT = 25


# ---------------------------------------------------------------------
# 1) NÚMERO ÓPTIMO DE RÉPLICAS
# ---------------------------------------------------------------------
def numero_optimo_replicas(n0=15, precision_relativa=0.05, confianza=0.95):
    """
    Corre un piloto de n0 réplicas sobre el escenario óptimo y estima,
    mediante la fórmula iterativa de Law (2015) basada en la
    distribución t de Student, cuántas réplicas serían necesarias para
    alcanzar una precisión relativa dada (por defecto, 5% de la media)
    con el nivel de confianza especificado (por defecto, 95%).
    """
    demoras = []
    for i in range(n0):
        semilla = 9000 + i * 137
        inter = ejecutar_motor(VERDE_NS_OPT, VERDE_EO_OPT, cfg.TIEMPO_SIMULACION, semilla)
        demoras.append(np.mean(inter.demoras))

    demoras = np.array(demoras)
    xbar = demoras.mean()
    s = demoras.std(ddof=1)
    E = precision_relativa * xbar

    alpha = 1 - confianza
    t_val = stats.t.ppf(1 - alpha / 2, df=n0 - 1)
    n_requerido = int(np.ceil((t_val * s / E) ** 2))

    return {
        "n0": n0, "demoras_piloto": demoras,
        "xbar_piloto": xbar, "s_piloto": s,
        "E_objetivo_seg": E, "t_valor": t_val,
        "n_requerido": n_requerido,
        "n0_suficiente": n0 >= n_requerido,
    }


# ---------------------------------------------------------------------
# 2) MONTE CARLO - PROPAGACIÓN DE INCERTIDUMBRE PARAMÉTRICA
# ---------------------------------------------------------------------
def monte_carlo_incertidumbre(n_iter=200, semilla_base=5000):
    """
    Muestrea los parámetros con mayor incertidumbre epistémica (asumidos
    por diseño, no calibrados con datos reales) y propaga su efecto sobre
    la demora promedio y el CO2 total, usando el escenario óptimo (40/25).
    """
    rng = np.random.default_rng(42)
    resultados_demora, resultados_co2 = [], []

    base_tasa = copy.deepcopy(cfg.TASA_BASE)
    base_tcm, base_tcd = cfg.TIEMPO_CRUCE_MEDIO, cfg.TIEMPO_CRUCE_DESV
    base_pico = cfg.FACTOR_PICO
    base_co2 = cfg.CO2_RATE_IDLE

    for i in range(n_iter):
        factor_demanda = rng.uniform(0.85, 1.15)
        cfg.TASA_BASE = {d: base_tasa[d] * factor_demanda for d in base_tasa}
        cfg.TIEMPO_CRUCE_MEDIO = base_tcm * rng.uniform(0.90, 1.10)
        cfg.TIEMPO_CRUCE_DESV = base_tcd * rng.uniform(0.80, 1.20)
        cfg.FACTOR_PICO = base_pico * rng.uniform(0.85, 1.15)
        cfg.CO2_RATE_IDLE = base_co2 * rng.uniform(0.80, 1.20)

        inter = ejecutar_motor(VERDE_NS_OPT, VERDE_EO_OPT, cfg.TIEMPO_SIMULACION,
                                semilla_base + i)
        resultados_demora.append(np.mean(inter.demoras))
        resultados_co2.append(inter.co2_total)

    # restaurar configuración original
    cfg.TASA_BASE = base_tasa
    cfg.TIEMPO_CRUCE_MEDIO, cfg.TIEMPO_CRUCE_DESV = base_tcm, base_tcd
    cfg.FACTOR_PICO = base_pico
    cfg.CO2_RATE_IDLE = base_co2

    demora = np.array(resultados_demora)
    co2 = np.array(resultados_co2)

    return {
        "n_iter": n_iter, "demora": demora, "co2": co2,
        "demora_media": demora.mean(), "demora_std": demora.std(ddof=1),
        "demora_p5": np.percentile(demora, 5), "demora_p95": np.percentile(demora, 95),
        "co2_media": co2.mean(), "co2_std": co2.std(ddof=1),
        "co2_p5": np.percentile(co2, 5), "co2_p95": np.percentile(co2, 95),
    }


# ---------------------------------------------------------------------
# 3) ANÁLISIS DE SENSIBILIDAD (one-at-a-time, +/-20%)
# ---------------------------------------------------------------------
def analisis_sensibilidad(delta=0.20, n_replicas=8):
    base_tasa = copy.deepcopy(cfg.TASA_BASE)
    base_tcm = cfg.TIEMPO_CRUCE_MEDIO
    base_pico = cfg.FACTOR_PICO
    base_co2 = cfg.CO2_RATE_IDLE

    def correr_promedio(n_rep=n_replicas):
        vals_demora, vals_co2 = [], []
        for i in range(n_rep):
            inter = ejecutar_motor(VERDE_NS_OPT, VERDE_EO_OPT, cfg.TIEMPO_SIMULACION,
                                    7000 + i * 53)
            vals_demora.append(np.mean(inter.demoras))
            vals_co2.append(inter.co2_total)
        return np.mean(vals_demora), np.mean(vals_co2)

    demora_base, co2_base = correr_promedio()

    variables = {
        "Tasa base de llegada (demanda)": "TASA_BASE",
        "Tiempo medio de cruce": "TIEMPO_CRUCE_MEDIO",
        "Factor de hora pico": "FACTOR_PICO",
        "Tasa de emisión CO2 (ralentí)": "CO2_RATE_IDLE",
    }

    resultados = []
    for nombre, attr in variables.items():
        for signo, etiqueta in [(1 + delta, f"+{int(delta*100)}%"), (1 - delta, f"-{int(delta*100)}%")]:
            if attr == "TASA_BASE":
                cfg.TASA_BASE = {d: base_tasa[d] * signo for d in base_tasa}
            elif attr == "TIEMPO_CRUCE_MEDIO":
                cfg.TIEMPO_CRUCE_MEDIO = base_tcm * signo
            elif attr == "FACTOR_PICO":
                cfg.FACTOR_PICO = base_pico * signo
            elif attr == "CO2_RATE_IDLE":
                cfg.CO2_RATE_IDLE = base_co2 * signo

            demora_i, co2_i = correr_promedio()
            resultados.append({
                "variable": nombre, "variacion": etiqueta,
                "demora": demora_i, "delta_demora_%": 100 * (demora_i - demora_base) / demora_base,
                "co2": co2_i, "delta_co2_%": 100 * (co2_i - co2_base) / co2_base,
            })

            cfg.TASA_BASE = copy.deepcopy(base_tasa)
            cfg.TIEMPO_CRUCE_MEDIO = base_tcm
            cfg.FACTOR_PICO = base_pico
            cfg.CO2_RATE_IDLE = base_co2

    return demora_base, co2_base, resultados


# ---------------------------------------------------------------------
# GRÁFICAS
# ---------------------------------------------------------------------
def graficar_monte_carlo(mc, ruta="outputs/monte_carlo_incertidumbre.png"):
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))

    axes[0].hist(mc["demora"], bins=20, color="purple", edgecolor="white", alpha=0.85)
    axes[0].axvline(mc["demora_media"], color="crimson", linestyle="--",
                     label=f"Media: {mc['demora_media']:.1f} s")
    axes[0].set_title("Monte Carlo: Demora Promedio")
    axes[0].set_xlabel("Demora promedio (s)")
    axes[0].set_ylabel("Frecuencia")
    axes[0].legend()

    axes[1].hist(mc["co2"], bins=20, color="blue", edgecolor="white", alpha=0.85)
    axes[1].axvline(mc["co2_media"], color="crimson", linestyle="--",
                     label=f"Media: {mc['co2_media']:.1f} kg")
    axes[1].set_title("Monte Carlo: CO2 Total")
    axes[1].set_xlabel("CO2 total (kg)")
    axes[1].set_ylabel("Frecuencia")
    axes[1].legend()

    fig.suptitle("Propagación de Incertidumbre Paramétrica (n=%d, escenario 40/25)" % mc["n_iter"])
    fig.tight_layout()
    fig.savefig(ruta, dpi=120)
    return fig


def graficar_tornado(resultados, demora_base, ruta="outputs/tornado_sensibilidad.png"):
    """Diagrama de tornado: efecto de cada variable (+/-20%) sobre la demora."""
    variables = sorted(set(r["variable"] for r in resultados))
    filas = []
    for var in variables:
        pos = next(r["delta_demora_%"] for r in resultados if r["variable"] == var and "+" in r["variacion"])
        neg = next(r["delta_demora_%"] for r in resultados if r["variable"] == var and "-" in r["variacion"])
        filas.append((var, neg, pos))

    filas.sort(key=lambda x: abs(x[1]) + abs(x[2]))

    fig, ax = plt.subplots(figsize=(9, 4.5))
    y_pos = np.arange(len(filas))
    for i, (var, neg, pos) in enumerate(filas):
        ax.barh(i, pos, color="crimson", alpha=0.8)
        ax.barh(i, neg, color="steelblue", alpha=0.8)

    ax.set_yticks(y_pos)
    ax.set_yticklabels([f[0] for f in filas])
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Variación en la demora promedio (%)")
    ax.set_title("Análisis de Sensibilidad: Efecto de +/-20% en cada variable")
    fig.tight_layout()
    fig.savefig(ruta, dpi=120)
    return fig


# ---------------------------------------------------------------------
# REPORTE PRINCIPAL
# ---------------------------------------------------------------------
def reporte_completo():
    print("=" * 70)
    print("1) NÚMERO ÓPTIMO DE RÉPLICAS")
    print("=" * 70)
    r1 = numero_optimo_replicas()
    print(f"  Piloto: n0={r1['n0']}, media={r1['xbar_piloto']:.2f}s, "
          f"desv.est={r1['s_piloto']:.2f}s")
    print(f"  Precisión objetivo: E={r1['E_objetivo_seg']:.2f}s (5% de la media), "
          f"t={r1['t_valor']:.3f}")
    print(f"  Réplicas requeridas: n* = {r1['n_requerido']}")
    print(f"  ¿n0 fue suficiente? {'Sí' if r1['n0_suficiente'] else 'No'}")

    print()
    print("=" * 70)
    print("2) MONTE CARLO - PROPAGACIÓN DE INCERTIDUMBRE")
    print("=" * 70)
    r2 = monte_carlo_incertidumbre()
    print(f"  Iteraciones: {r2['n_iter']}")
    print(f"  Demora: media={r2['demora_media']:.2f}s, std={r2['demora_std']:.2f}s, "
          f"P5-P95=[{r2['demora_p5']:.2f}, {r2['demora_p95']:.2f}]s")
    print(f"  CO2:    media={r2['co2_media']:.2f}kg, std={r2['co2_std']:.2f}kg, "
          f"P5-P95=[{r2['co2_p5']:.2f}, {r2['co2_p95']:.2f}]kg")
    graficar_monte_carlo(r2)

    print()
    print("=" * 70)
    print("3) ANÁLISIS DE SENSIBILIDAD (+/-20%)")
    print("=" * 70)
    demora_base, co2_base, r3 = analisis_sensibilidad()
    print(f"  Base: demora={demora_base:.3f}s, co2={co2_base:.3f}kg")
    for row in r3:
        print(f"  {row['variable']:35s} {row['variacion']:>5s}  "
              f"demora={row['demora']:7.2f}s ({row['delta_demora_%']:+6.2f}%)   "
              f"co2={row['co2']:7.3f}kg ({row['delta_co2_%']:+6.2f}%)")
    graficar_tornado(r3, demora_base)

    print("\nGráficas guardadas en outputs/: monte_carlo_incertidumbre.png, tornado_sensibilidad.png")
    return r1, r2, r3


if __name__ == "__main__":
    reporte_completo()
