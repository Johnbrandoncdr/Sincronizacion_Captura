import os
import pandas as pd

# Ruta base donde están las carpetas (ajústala si es necesario)
base_path = "C:/Users/johnb/Documents/MICA/Sincronizacion_Captura"

# Subcarpetas a procesar
subfolders = [
    "imagenes_20250528_delay5ms_int32ms_espectrometro",
    "imagenes_20250528_delay5ms_int64ms_espectrometro",
    "imagenes_20250528_delay5ms_int160ms_espectrometro",
    "imagenes_20250528_delay5ms_int320ms_espectrometro",
    "imagenes_20250528_delay5ms_int640ms_espectrometro"
]

# Lista para almacenar resultados
resultados_picos = []

# Recorrer todas las carpetas
for carpeta in subfolders:
    carpeta_path = os.path.join(base_path, carpeta)

    for archivo in os.listdir(carpeta_path):
        if archivo.startswith("espectro_") and archivo.endswith(".csv"):
            file_path = os.path.join(carpeta_path, archivo)

            try:
                df = pd.read_csv(file_path)
                idx_max = df["Intensidad"].idxmax()
                longitud_pico = df.loc[idx_max, "Longitud de onda (nm)"]
                
                resultados_picos.append({
                    "Carpeta": carpeta,
                    "Archivo": archivo,
                    "Longitud de onda pico (nm)": longitud_pico,
                })
            except Exception as e:
                print(f"⚠️ Error procesando {file_path}: {e}")

# Crear DataFrame final
df_resultados = pd.DataFrame(resultados_picos)

# Extraer el número de imagen desde el nombre del archivo
df_resultados["Num archivo"] = df_resultados["Archivo"].str.extract(r"espectro_(\d+)_")[0].astype(int)

# Ordenar por carpeta y número de archivo
df_resultados = df_resultados.sort_values(by=["Carpeta", "Num archivo"]).reset_index(drop=True)

# Guardar CSV ordenado
df_resultados.to_csv("picos_espectrales.csv", index=False)
print(df_resultados)
