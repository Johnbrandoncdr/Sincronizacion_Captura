import os
import pandas as pd
import matplotlib.pyplot as plt
from scipy.signal import savgol_filter

# ============================
# CONFIGURACIÓN
# ============================
base_path = "C:/Users/johnb/Documents/MICA/Sincronizacion_Captura"

subfolders = [
    "imagenes_20250603_delay5ms_int32ms_espectrometro",
]

suavizados_dict = {}
resultados_picos = []

# ============================
# PROCESAMIENTO Y GRAFICADO
# ============================
for carpeta in subfolders:
    carpeta_path = os.path.join(base_path, carpeta)

    # Crear carpeta para guardar gráficas
    graficas_path = os.path.join(base_path, "graficas_resultado", carpeta)
    os.makedirs(graficas_path, exist_ok=True)

    for archivo in sorted(os.listdir(carpeta_path)):
        if archivo.startswith("espectro_") and archivo.endswith(".csv"):
            file_path = os.path.join(carpeta_path, archivo)

            try:
                df = pd.read_csv(file_path)
                df = df[(df["Longitud de onda (nm)"] > 310) & (df["Longitud de onda (nm)"] < 690)].copy()

                # Suavizado robusto
                df["Suavizado"] = savgol_filter(df["Intensidad"], window_length=51, polyorder=3)

                # Guardar espectro suavizado
                suavizados_dict[archivo] = df

                # Detectar pico más alto del suavizado
                idx_max = df["Suavizado"].idxmax()
                longitud_pico = df.loc[idx_max, "Longitud de onda (nm)"]

                # Guardar resultado
                resultados_picos.append({
                    "Carpeta": carpeta,
                    "Archivo": archivo,
                    "Longitud de onda pico (nm)": round(longitud_pico, 2),
                })

                # Mostrar y guardar gráfica
                plt.figure(figsize=(8, 4))
                plt.plot(df["Longitud de onda (nm)"], df["Intensidad"], label="Original", alpha=0.4)
                plt.plot(df["Longitud de onda (nm)"], df["Suavizado"], label="Suavizado", linewidth=2)
                plt.axvline(longitud_pico, color="red", linestyle="--", label=f"Pico: {longitud_pico:.2f} nm")
                plt.title(f"{archivo}")
                plt.xlabel("Longitud de onda (nm)")
                plt.ylabel("Intensidad")
                plt.legend()
                plt.grid(True)
                plt.tight_layout()

                # Guardar imagen
                nombre_png = archivo.replace(".csv", ".png")
                plt.savefig(os.path.join(graficas_path, nombre_png))

            except Exception as e:
                print(f"Error procesando {file_path}: {e}")

# ============================
# GUARDAR RESULTADOS
# ============================
df_resultados = pd.DataFrame(resultados_picos)
df_resultados["Num archivo"] = df_resultados["Archivo"].str.extract(r"espectro_(\d+)_")[0].astype(int)
df_resultados = df_resultados.sort_values(by="Num archivo").reset_index(drop=True)

# Guardar archivo CSV
output_csv = os.path.join(base_path, "picos_espectrales.csv")
df_resultados.to_csv(output_csv, index=False)

print("\nResultados guardados en picos_espectrales.csv")
print(df_resultados)
