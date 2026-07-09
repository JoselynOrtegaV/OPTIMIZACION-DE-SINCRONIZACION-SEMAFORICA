"""
bondad_ajuste.py
----------------
Valida estadísticamente que los supuestos estocásticos del modelo son
razonables:
  1) Los tiempos ENTRE LLEGADAS de vehículos (en tramos de tasa
     aproximadamente constante) deben ajustarse a una distribución
     EXPONENCIAL (propio de un proceso de Poisson).
  2) Los tiempos de CRUCE de la intersección deben ajustarse a una
     distribución NORMAL.

Se usan dos pruebas clásicas de bondad de ajuste:
  - Kolmogorov-Smirnov (KS): compara la función de distribución empírica
    contra la teórica.
  - Chi-cuadrado: compara frecuencias observadas vs esperadas por bins.

Ambas pruebas devuelven un estadístico y un p-valor. Con un nivel de
significancia usual de alpha = 0.05, si p-valor > alpha NO se rechaza la
hipótesis nula (los datos SÍ son consistentes con la distribución teórica).
"""

import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

import config as cfg


def _es_tramo_estable(t):
    """
    True si el instante t (segundos) cae FUERA de la hora pico y sus
    rampas de transición, es decir, en un tramo donde lambda(t) es
    aproximadamente constante (proceso de Poisson homogéneo por tramos).
    """
    minuto = t / 60.0
    inicio_rampa = cfg.PICO_INICIO_MIN - cfg.RAMPA_MIN
    fin_rampa = cfg.PICO_FIN_MIN + cfg.RAMPA_MIN
    return not (inicio_rampa <= minuto <= fin_rampa)


def prueba_ks(datos, distribucion, parametros):
    """
    Prueba de Kolmogorov-Smirnov.
    distribucion: nombre de distribución de scipy.stats (ej. 'expon', 'norm')
    parametros: tupla de parámetros (loc, scale) de esa distribución

    Nota técnica: se usa una distribución "congelada" (frozen) en vez de
    pasar los parámetros vía `args=`, porque en algunas combinaciones de
    versiones de scipy/Python (p.ej. Python 3.14 muy reciente) la firma
    interna de `kstest` con `args=` puede fallar. Usar `frozen.cdf` como
    función de comparación es la forma más robusta y evita ese problema.
    """
    dist = getattr(stats, distribucion)
    frozen = dist(*parametros)
    estadistico, p_valor = stats.kstest(datos, frozen.cdf)
    return estadistico, p_valor


def prueba_chi_cuadrado(datos, distribucion, parametros, bins=10):
    """
    Prueba de Chi-cuadrado de bondad de ajuste, agrupando los datos en
    `bins` intervalos y comparando frecuencias observadas vs esperadas.
    """
    frec_obs, bordes = np.histogram(datos, bins=bins)
    dist = getattr(stats, distribucion)

    # Probabilidad teórica de caer en cada intervalo
    cdf_bordes = dist.cdf(bordes, *parametros)
    prob_intervalo = np.diff(cdf_bordes)
    prob_intervalo[prob_intervalo <= 0] = 1e-10  # evitar división por cero
    frec_esp = prob_intervalo * len(datos)

    estadistico, p_valor = stats.chisquare(frec_obs, f_exp=frec_esp * (frec_obs.sum() / frec_esp.sum()))
    return estadistico, p_valor


def analizar_tiempos_entre_llegadas(interseccion, direccion="E", alpha=0.05):
    """
    Ajusta los tiempos entre llegadas aceptadas, RESTRINGIDOS al tramo
    donde lambda(t) es aproximadamente constante (fuera de la hora pico
    y sus rampas), a una distribución Exponencial, y corre las pruebas
    de bondad de ajuste KS y Chi-cuadrado. Esta restricción es necesaria
    porque el proceso completo es un Poisson NO homogéneo: solo dentro de
    un tramo de tasa constante es correcto esperar un ajuste Exponencial.
    """
    pares = interseccion.tiempos_entre_llegadas[direccion]
    datos = np.array([dt for (t, dt) in pares if _es_tramo_estable(t) and dt > 0])

    # Ajuste de máxima verosimilitud de la Exponencial (loc fijo en 0)
    loc, scale = stats.expon.fit(datos, floc=0)

    # Número de bins adaptativo: se busca frecuencia esperada >= 5 por bin
    # (regla práctica para que la prueba Chi-cuadrado sea válida)
    bins = max(4, min(12, len(datos) // 8))

    ks_stat, ks_p = prueba_ks(datos, "expon", (loc, scale))
    chi_stat, chi_p = prueba_chi_cuadrado(datos, "expon", (loc, scale), bins=bins)

    resultado = {
        "direccion": direccion,
        "n": len(datos),
        "lambda_estimado": 1 / scale,
        "ks_estadistico": ks_stat, "ks_p_valor": ks_p, "ks_ajusta": ks_p > alpha,
        "chi2_estadistico": chi_stat, "chi2_p_valor": chi_p, "chi2_ajusta": chi_p > alpha,
    }
    return resultado, datos, ("expon", (loc, scale))


def analizar_tiempos_cruce(interseccion, alpha=0.05):
    """
    Ajusta los tiempos de cruce a una distribución Normal y corre las
    pruebas de bondad de ajuste KS y Chi-cuadrado.
    """
    datos = np.array(interseccion.tiempos_cruce)

    mu, sigma = stats.norm.fit(datos)

    ks_stat, ks_p = prueba_ks(datos, "norm", (mu, sigma))
    chi_stat, chi_p = prueba_chi_cuadrado(datos, "norm", (mu, sigma), bins=12)

    resultado = {
        "n": len(datos),
        "mu_estimado": mu, "sigma_estimado": sigma,
        "ks_estadistico": ks_stat, "ks_p_valor": ks_p, "ks_ajusta": ks_p > alpha,
        "chi2_estadistico": chi_stat, "chi2_p_valor": chi_p, "chi2_ajusta": chi_p > alpha,
    }
    return resultado, datos, ("norm", (mu, sigma))


def graficar_bondad_ajuste(datos, distribucion, parametros, titulo, ruta_salida=None):
    """Histograma de los datos observados vs la densidad teórica ajustada."""
    dist = getattr(stats, distribucion)

    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.hist(datos, bins=15, density=True, alpha=0.6, color="steelblue",
            edgecolor="white", label="Datos observados")

    x = np.linspace(min(datos), max(datos), 200)
    ax.plot(x, dist.pdf(x, *parametros), color="crimson", lw=2,
            label=f"Ajuste teórico ({distribucion})")

    ax.set_title(titulo)
    ax.set_xlabel("Valor (segundos)")
    ax.set_ylabel("Densidad")
    ax.legend()
    fig.tight_layout()

    if ruta_salida:
        fig.savefig(ruta_salida, dpi=120)
    return fig


def reporte_bondad_ajuste(interseccion, direccion_llegadas="E", alpha=0.05,
                           carpeta_salida="outputs"):
    """
    Corre el análisis completo de bondad de ajuste (llegadas + cruce),
    imprime un reporte en consola y guarda las gráficas comparativas.
    """
    print("=" * 60)
    print("ANÁLISIS DE BONDAD DE AJUSTE")
    print("=" * 60)

    r_llegadas, datos_llegadas, dist_llegadas = analizar_tiempos_entre_llegadas(
        interseccion, direccion=direccion_llegadas, alpha=alpha)
    print(f"\n[1] Tiempos entre llegadas (dirección {direccion_llegadas}) vs EXPONENCIAL")
    print(f"    n = {r_llegadas['n']}, lambda estimado = {r_llegadas['lambda_estimado']:.4f} veh/seg")
    print(f"    KS:     estadístico={r_llegadas['ks_estadistico']:.4f}  p-valor={r_llegadas['ks_p_valor']:.4f}"
          f"  -> {'SE AJUSTA' if r_llegadas['ks_ajusta'] else 'NO se ajusta'} (alpha={alpha})")
    print(f"    Chi2:   estadístico={r_llegadas['chi2_estadistico']:.4f}  p-valor={r_llegadas['chi2_p_valor']:.4f}"
          f"  -> {'SE AJUSTA' if r_llegadas['chi2_ajusta'] else 'NO se ajusta'} (alpha={alpha})")

    graficar_bondad_ajuste(
        datos_llegadas, *dist_llegadas,
        titulo=f"Bondad de Ajuste: Tiempos entre Llegadas (dirección {direccion_llegadas})",
        ruta_salida=f"{carpeta_salida}/bondad_ajuste_llegadas.png")

    r_cruce, datos_cruce, dist_cruce = analizar_tiempos_cruce(interseccion, alpha=alpha)
    print(f"\n[2] Tiempos de cruce vs NORMAL")
    print(f"    n = {r_cruce['n']}, mu={r_cruce['mu_estimado']:.3f}s, sigma={r_cruce['sigma_estimado']:.3f}s")
    print(f"    KS:     estadístico={r_cruce['ks_estadistico']:.4f}  p-valor={r_cruce['ks_p_valor']:.4f}"
          f"  -> {'SE AJUSTA' if r_cruce['ks_ajusta'] else 'NO se ajusta'} (alpha={alpha})")
    print(f"    Chi2:   estadístico={r_cruce['chi2_estadistico']:.4f}  p-valor={r_cruce['chi2_p_valor']:.4f}"
          f"  -> {'SE AJUSTA' if r_cruce['chi2_ajusta'] else 'NO se ajusta'} (alpha={alpha})")

    graficar_bondad_ajuste(
        datos_cruce, *dist_cruce,
        titulo="Bondad de Ajuste: Tiempos de Cruce",
        ruta_salida=f"{carpeta_salida}/bondad_ajuste_cruce.png")

    print("\nGráficas guardadas en la carpeta:", carpeta_salida)
    return r_llegadas, r_cruce
