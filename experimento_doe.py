"""
experimento_doe.py
------------------
Diseño de experimentos (DOE): corre el motor de eventos discretos con
distintas combinaciones de tiempos de verde (NS x EO) y compara la
demora promedio y las emisiones de CO2 resultantes.
"""

import itertools
import csv
from collections import defaultdict, Counter
import numpy as np
import matplotlib.pyplot as plt

import config as cfg
from motor_eventos import ejecutar_motor


def cola_promedio_por_direccion(interseccion):
    """
    Calcula, a partir de interseccion.serie_colas (t, direccion, cola),
    la longitud de cola promedio observada en cada dirección durante
    esa corrida.
    """
    muestras = defaultdict(list)
    for _, direccion, cola in interseccion.serie_colas:
        muestras[direccion].append(cola)
    return {d: float(np.mean(v)) for d, v in muestras.items() if v}


def correr_experimento(tiempos_ns=cfg.TIEMPOS_VERDE_NS, tiempos_eo=cfg.TIEMPOS_VERDE_EO,
                        tiempo_simulacion=cfg.TIEMPO_SIMULACION, n_replicas=10):
    resultados = []

    for verde_ns, verde_eo in itertools.product(tiempos_ns, tiempos_eo):
        replicas_demora = []
        replicas_co2 = []
        replicas_vehiculos = []
        replicas_cola_max = []           # peor cola promedio (cuello de botella) por réplica
        replicas_direccion_critica = []  # qué dirección fue la más congestionada esa réplica

        for i in range(n_replicas):
            semilla_dinamica = cfg.SEMILLA + (i * 100)
            interseccion = ejecutar_motor(verde_ns, verde_eo, tiempo_simulacion, semilla_dinamica)

            if interseccion.demoras:
                replicas_demora.append(np.mean(interseccion.demoras))
            else:
                replicas_demora.append(0.0)
            replicas_co2.append(interseccion.co2_total)
            replicas_vehiculos.append(len(interseccion.demoras))

            promedios_direccion = cola_promedio_por_direccion(interseccion)
            if promedios_direccion:
                direccion_critica = max(promedios_direccion, key=promedios_direccion.get)
                replicas_cola_max.append(promedios_direccion[direccion_critica])
                replicas_direccion_critica.append(direccion_critica)
            else:
                replicas_cola_max.append(0.0)

        demora_media = float(np.mean(replicas_demora))
        desv_est = float(np.std(replicas_demora, ddof=1)) if n_replicas > 1 else 0.0
        error_estandar = desv_est / np.sqrt(n_replicas)
        intervalo_95 = 1.96 * error_estandar

        direccion_mas_frecuente = (Counter(replicas_direccion_critica).most_common(1)[0][0]
                                    if replicas_direccion_critica else "-")

        resultados.append({
            "verde_ns": verde_ns,
            "verde_eo": verde_eo,
            "n_vehiculos": int(np.mean(replicas_vehiculos)),
            "demora_promedio": demora_media,
            "ic_95_inf": max(0.0, demora_media - intervalo_95),
            "ic_95_sup": demora_media + intervalo_95,
            "co2_total_kg": float(np.mean(replicas_co2)),
            "cola_promedio_max": float(np.mean(replicas_cola_max)),
            "direccion_critica": direccion_mas_frecuente,
        })

    resultados.sort(key=lambda r: r["demora_promedio"])
    return resultados


def guardar_csv(resultados, ruta="outputs/resultados_doe.csv"):
    campos = list(resultados[0].keys())
    with open(ruta, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=campos)
        writer.writeheader()
        writer.writerows(resultados)


def graficar_doe(resultados, ruta="outputs/doe_demora_promedio.png"):
    etiquetas = [f"{r['verde_ns']}/{r['verde_eo']}" for r in resultados]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    
    medios = [r["demora_promedio"] for r in resultados]
    inf = [r["ic_95_inf"] for r in resultados]
    sup = [r["ic_95_sup"] for r in resultados]
    errores = [sup[i] - medios[i] for i in range(len(resultados))]
    
    ax.bar(etiquetas, medios, yerr=errores, color="steelblue", capsize=5, ecolor="crimson")
    ax.set_title("Demora Promedio con Intervalos de Confianza del 95% (Verde NS / Verde EO)")
    ax.set_xlabel("Combinación (s)")
    ax.set_ylabel("Demora Promedio (s)")
    plt.xticks(rotation=45)
    fig.tight_layout()
    fig.savefig(ruta, dpi=120)
    return fig


def imprimir_tabla(resultados):
    print(f"{'NS':>4} {'EO':>4} {'#veh':>6} {'demora_prom(s)':>16} {'IC 95% (Inf - Sup)':>24} "
          f"{'CO2(kg)':>10} {'cola_max(veh)':>14} {'dir_critica':>12}")
    for r in resultados:
        print(f"{r['verde_ns']:>4} {r['verde_eo']:>4} {r['n_vehiculos']:>6} "
              f"{r['demora_promedio']:>16.2f}   [{r['ic_95_inf']:.2f} - {r['ic_95_sup']:.2f}] "
              f"{r['co2_total_kg']:>10.3f} {r['cola_promedio_max']:>14.2f} {r['direccion_critica']:>12}")

    mejor = resultados[0]
    base = next((r for r in resultados if r["verde_ns"] == cfg.VERDE_NS and r["verde_eo"] == cfg.VERDE_EO), None)

    print(f"\n>> Mejor combinación: NS={mejor['verde_ns']}s / EO={mejor['verde_eo']}s "
          f"(demora promedio = {mejor['demora_promedio']:.2f}s, CO2 = {mejor['co2_total_kg']:.3f} kg, "
          f"cola crítica = {mejor['cola_promedio_max']:.2f} veh en dirección {mejor['direccion_critica']})")

    if base and base is not mejor:
        reduccion_cola = 100 * (base["cola_promedio_max"] - mejor["cola_promedio_max"]) / base["cola_promedio_max"]
        print(f">> EL PROBLEMA (config. base {base['verde_ns']}/{base['verde_eo']}): "
              f"cola crítica = {base['cola_promedio_max']:.2f} veh en dirección {base['direccion_critica']}")
        print(f">> LA SOLUCIÓN (config. óptima {mejor['verde_ns']}/{mejor['verde_eo']}): "
              f"cola crítica = {mejor['cola_promedio_max']:.2f} veh -> reducción del {reduccion_cola:.1f}%")


if __name__ == "__main__":
    resultados = correr_experimento(n_replicas=10)
    imprimir_tabla(resultados)
    guardar_csv(resultados)
    graficar_doe(resultados)