import serial
import os
import datetime
import time
from pypylon import pylon
import cv2
import numpy as np
import pandas as pd
from seabreeze.spectrometers import Spectrometer

# ============================
# Parámetros Generales
# ============================
delay_entre_fotos_ms = 5        # Milisegundos de espera antes de cada captura
tiempo_integracion_ms = 32      # Tiempo de exposición de la cámara (ms)
espera_post_final_ms = 500      # Espera final antes de terminar todo (ms)
TOTAL_FOTOS = 20

# ============================
# Crear carpetas de salida
# ============================
timestamp_folder = datetime.datetime.now().strftime("%Y%m%d")
timestamp_folder += f"_delay{delay_entre_fotos_ms}ms_int{tiempo_integracion_ms}ms_espectrometro"
fecha_hoy = datetime.datetime.now().strftime("%Y%m%d")
output_folder = f'imagenes_{timestamp_folder}'
os.makedirs(output_folder, exist_ok=True)

# ============================
# Inicializar cámara
# ============================
camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.Open()
camera.ExposureTime.SetValue(tiempo_integracion_ms * 1000)  # µs
actual_exposure = camera.ExposureTime.GetValue()
print(f"Tiempo de integración aplicado: {actual_exposure} µs")
camera.StartGrabbing(pylon.GrabStrategy_OneByOne)

converter = pylon.ImageFormatConverter()
converter.OutputPixelFormat = pylon.PixelType_BGR8packed
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

# ============================
# Inicializar espectrómetro
# ============================
# espectro = Spectrometer.from_first_available()
# espectro.integration_time_micros(tiempo_integracion_ms * 1000)  # configurar igual que la cámara
# longitudes_onda = espectro.wavelengths()
# print("Espectrómetro conectado")

# ============================
# Conexión Arduino
# ============================
arduino = serial.Serial('COM5', 9600, timeout=1)
print(f"Conectado al Arduino\n Guardando imágenes y espectros en: {output_folder}")

# ============================
# Espera a home
# ============================
while True:
    linea = arduino.readline().decode('utf-8').strip()
    if linea.startswith("ready|"):
        print("Arduino confirmó posición inicial.")
        arduino.write(b"ok\n")
        break

# ============================
# Captura de imágenes y espectros
# ============================
resultados = []
contador_fotos = 0
tiempo_inicio_global = time.perf_counter()

linea = arduino.readline().decode('utf-8').strip()
angulo = float(linea.split("|")[1]) if "capturar|" in linea else None

try:
    while contador_fotos < TOTAL_FOTOS:
        if contador_fotos > 0 or angulo is not None:
            print(f"\nCapturando foto {contador_fotos + 1} en ángulo {angulo:.2f}°")

            print(f"Esperando {delay_entre_fotos_ms} ms antes de capturar")
            time.sleep(delay_entre_fotos_ms / 1000)

            # Reiniciar captura para asegurar imagen nueva
            camera.StopGrabbing()
            camera.StartGrabbing(pylon.GrabStrategy_OneByOne)

            start_time = time.perf_counter()
            grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

            if grabResult.GrabSucceeded():
                image = converter.Convert(grabResult)
                img = image.GetArray()

                mean_val = np.mean(img)

                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                img_filename = os.path.join(output_folder, f'foto_{contador_fotos + 1}_{fecha_hoy}.bmp')
                cv2.imwrite(img_filename, img)

                # # Capturar espectro
                # intensidades = espectro.intensities()
                # espectro_filename = os.path.join(output_folder, f'espectro_{contador_fotos + 1}_{fecha_hoy}.csv')
                # df_espectro = pd.DataFrame({
                #     'Longitud de onda (nm)': longitudes_onda,
                #     'Intensidad': intensidades
                # })
                # df_espectro.to_csv(espectro_filename, index=False)
                # print(f"Espectro guardado: {espectro_filename}")

                end_time = time.perf_counter()
                tiempo_total = (end_time - start_time) * 1000  # en ms
                tiempo_sistema = tiempo_total - tiempo_integracion_ms
                resolucion_temporal = tiempo_total + delay_entre_fotos_ms

                resultados.append({
                    "Foto": contador_fotos + 1,
                    "Timestamp": timestamp,
                    "Ángulo (°)": round(angulo, 2),
                    "Tiempo integración (ms)": tiempo_integracion_ms,
                    "Tiempo sistema sin integración (ms)": round(tiempo_sistema, 2),
                    "Delay entre fotos (ms)": delay_entre_fotos_ms,
                    "Tiempo total captura (ms)": round(tiempo_total, 2),
                    "Resolución temporal real (ms)": round(resolucion_temporal, 2),
                    "Media intensidad": round(mean_val, 2),
                })

                arduino.write(b"ok\n")
                contador_fotos += 1
                print(f"Foto {contador_fotos} guardada como: {img_filename}")

                if contador_fotos == TOTAL_FOTOS:
                    print("Esperando finalización...")
                    time.sleep(espera_post_final_ms / 1000)

                if contador_fotos < TOTAL_FOTOS:
                    linea = arduino.readline().decode('utf-8').strip()
                    angulo = float(linea.split("|")[1]) if "capturar|" in linea else None

            grabResult.Release()

except KeyboardInterrupt:
    print("Programa detenido manualmente")

finally:
    tiempo_fin_global = time.perf_counter()
    tiempo_total_experimento_ms = (tiempo_fin_global - tiempo_inicio_global) * 1000

    camera.StopGrabbing()
    camera.Close()
    # espectro.close()
    arduino.close()
    print("Recursos liberados correctamente")

    # ============================
    # Guardar CSV resumen
    # ============================
    csv_path = os.path.join(output_folder, f"tiempos_adquisicion_{timestamp_folder}.csv")
    df = pd.DataFrame(resultados)

    promedio_total = df["Tiempo total captura (ms)"].mean()
    promedio_sistema = df["Tiempo sistema sin integración (ms)"].mean()
    promedio_resolucion = df["Resolución temporal real (ms)"].mean()

    resumen = {
        "Foto": "RESUMEN",
        "Timestamp": "-",
        "Ángulo (°)": "-",
        "Tiempo integración (ms)": tiempo_integracion_ms,
        "Tiempo sistema sin integración (ms)": round(promedio_sistema, 2),
        "Delay entre fotos (ms)": delay_entre_fotos_ms,
        "Tiempo total captura (ms)": round(promedio_total, 2),
        "Resolución temporal real (ms)": round(promedio_resolucion, 2),
        "Media intensidad": round(df["Media intensidad"].mean(), 2),
    }

    total_row = {
        "Foto": "TOTAL",
        "Timestamp": "-",
        "Ángulo (°)": "-",
        "Tiempo integración (ms)": "-",
        "Tiempo sistema sin integración (ms)": "-",
        "Delay entre fotos (ms)": "-",
        "Tiempo total captura (ms)": round(tiempo_total_experimento_ms, 2),
        "Resolución temporal real (ms)": "-",
        "Media intensidad": "-",
    }

    df.loc[len(df)] = resumen
    df.loc[len(df)] = total_row
    df.to_csv(csv_path, index=False)

    print(f"\nResultados guardados en: {csv_path}")
