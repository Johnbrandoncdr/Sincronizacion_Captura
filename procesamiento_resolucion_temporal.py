import pandas as pd
import os

# Diccionario con los archivos por tiempo de integración
archivos = {
    32: "imagenes_20250528_delay5ms_int32ms_espectrometro/tiempos_adquisicion_20250528_delay5ms_int32ms_espectrometro.csv",
    64: "imagenes_20250528_delay5ms_int64ms_espectrometro/tiempos_adquisicion_20250528_delay5ms_int64ms_espectrometro.csv",
    160: "imagenes_20250528_delay5ms_int160ms_espectrometro/tiempos_adquisicion_20250528_delay5ms_int160ms_espectrometro.csv",
    320: "imagenes_20250528_delay5ms_int320ms_espectrometro/tiempos_adquisicion_20250528_delay5ms_int320ms_espectrometro.csv",
    640: "imagenes_20250528_delay5ms_int640ms_espectrometro/tiempos_adquisicion_20250528_delay5ms_int640ms_espectrometro.csv"
}

# Ruta base
base_path = "C:/Users/johnb/Documents/MICA/Sincronizacion_Captura"

# Lista para resultados
tabla_tiempos = []

# Procesar cada archivo
for tiempo_integracion, filename in archivos.items():
    df = pd.read_csv(os.path.join(base_path, filename))
    df = df[df["Foto"].apply(lambda x: str(x).isdigit())]  # filtrar solo fotos numéricas

    tiempo_promedio = df["Tiempo total captura (ms)"].mean()
    tiempo_total = df["Tiempo total captura (ms)"].sum() / 1000  # convertir a segundos

    tabla_tiempos.append({
        "Tiempo de integración (ms)": tiempo_integracion,
        "Tiempo promedio por imagen (ms)": round(tiempo_promedio, 2),
        "Tiempo total para 20 imágenes (s)": round(tiempo_total, 2)
    })

df_tiempos = pd.DataFrame(tabla_tiempos).sort_values("Tiempo de integración (ms)")
df_tiempos.to_csv("resolucion_temporal.csv", index=False)