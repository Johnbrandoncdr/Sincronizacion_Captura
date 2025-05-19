import serial
import os
import datetime
import time
from pypylon import pylon
import cv2
import numpy as np
import pandas as pd
from threading import Thread

# Control configurable del tiempo entre fotos
delay_entre_fotos = 0.1  # segundos de espera después de cada captura
espera_post_final = 1.0  # segundos después de la última captura
stacking = 1  # número de imágenes por paso

def stack_images(images):
    return np.mean(images, axis=0).astype(np.uint8)

def guardar_imagen_en_hilo(img, filename):
    Thread(target=lambda: cv2.imwrite(filename, img)).start()

# Crear carpeta con nombre basado en fecha y hora
timestamp_folder = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
output_folder = f'imagenes_{timestamp_folder}'
os.makedirs(output_folder, exist_ok=True)

# Inicializar cámara
camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.Open()
camera.StartGrabbing(pylon.GrabStrategy_OneByOne)

# Configurar convertidor de imagen
converter = pylon.ImageFormatConverter()
converter.OutputPixelFormat = pylon.PixelType_BGR8packed
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

# Conectar al puerto serial del Arduino
arduino = serial.Serial('COM5', 9600, timeout=1)
print(f"Conectado al Arduino\n Guardando imágenes en: {output_folder}")

# Lista para guardar tiempos
resultados = []
contador_fotos = 0
TOTAL_FOTOS = 20

# Leer mensaje de ángulo para la primera imagen
linea = arduino.readline().decode('utf-8').strip()
if linea.startswith("capturar|"):
    try:
        partes = linea.split("|")
        angulo = float(partes[1])
    except (IndexError, ValueError):
        angulo = None
else:
    angulo = None

# Captura inicial con stacking
imagenes_stack = []
start_time = time.perf_counter()
for _ in range(stacking):
    grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
    if grabResult.GrabSucceeded():
        image = converter.Convert(grabResult)
        img = image.GetArray()
        imagenes_stack.append(img)
    grabResult.Release()
    time.sleep(0.05)

imagen_final = stack_images(imagenes_stack)
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
filename = os.path.join(output_folder, f'foto_{timestamp}.bmp')
guardar_imagen_en_hilo(imagen_final, filename)

arduino.write(b"ok\n")
time.sleep(delay_entre_fotos)

end_time = time.perf_counter()
tiempo_total = (end_time - start_time) * 1000

resultados.append({
    "Foto": contador_fotos + 1,
    "Timestamp": timestamp,
    "Tiempo total (ms)": round(tiempo_total, 2),
    "Retraso aprox. sincronización (ms)": round(tiempo_total - 32, 2),
    "Ángulo (°)": round(angulo, 2) if angulo is not None else "N/A",
})
contador_fotos += 1

# Captura del resto de imágenes
try:
    while contador_fotos < TOTAL_FOTOS:
        if arduino.in_waiting > 0:
            linea = arduino.readline().decode('utf-8').strip()
            if linea.startswith("capturar|"):
                try:
                    partes = linea.split("|")
                    angulo = float(partes[1])
                except (IndexError, ValueError):
                    angulo = None

                print(f"Capturando {stacking} imágenes para paso {contador_fotos + 1}...")

                imagenes_stack = []
                start_time = time.perf_counter()
                for _ in range(stacking):
                    grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)
                    if grabResult.GrabSucceeded():
                        image = converter.Convert(grabResult)
                        img = image.GetArray()
                        imagenes_stack.append(img)
                    grabResult.Release()
                    time.sleep(0.05)

                imagen_final = stack_images(imagenes_stack)
                timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                filename = os.path.join(output_folder, f'foto_{timestamp}.bmp')
                guardar_imagen_en_hilo(imagen_final, filename)

                arduino.write(b"ok\n")
                time.sleep(delay_entre_fotos)
                end_time = time.perf_counter()
                tiempo_total = (end_time - start_time) * 1000

                resultados.append({
                    "Foto": contador_fotos + 1,
                    "Timestamp": timestamp,
                    "Tiempo total (ms)": round(tiempo_total, 2),
                    "Retraso aprox. sincronización (ms)": round(tiempo_total - 32, 2),
                    "Ángulo (°)": round(angulo, 2) if angulo is not None else "N/A",
                })

                contador_fotos += 1
                print(f"Foto guardada: {filename} (Total fotos: {contador_fotos})")

                if contador_fotos == TOTAL_FOTOS:
                    print("Esperando antes de volver al inicio...")
                    time.sleep(espera_post_final)

except KeyboardInterrupt:
    print("Programa detenido manualmente")

finally:
    camera.StopGrabbing()
    camera.Close()
    arduino.close()
    print("Recursos liberados correctamente")

    # Guardar resultados como CSV en la misma carpeta
    csv_path = os.path.join(output_folder, f"tiempos_adquisicion_{timestamp_folder}.csv")
    df = pd.DataFrame(resultados)
    df.to_csv(csv_path, index=False)
    print(f"Resultados guardados en '{csv_path}'")
