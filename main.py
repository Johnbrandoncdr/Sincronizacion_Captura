import serial
import os
import datetime
from pypylon import pylon
import cv2
import numpy as np

# Conectar al puerto serial del Arduino
arduino = serial.Serial('COM5', 9600, timeout=1)
print("✅ Conectado al Arduino")

# Crear carpeta 'imagenes' si no existe
output_folder = 'imagenes'
os.makedirs(output_folder, exist_ok=True)

# Inicializar cámara
camera = pylon.InstantCamera(pylon.TlFactory.GetInstance().CreateFirstDevice())
camera.Open()

# Modo captura continua
camera.StartGrabbing(pylon.GrabStrategy_LatestImageOnly)

# Configurar convertidor de imagen
converter = pylon.ImageFormatConverter()
converter.OutputPixelFormat = pylon.PixelType_BGR8packed
converter.OutputBitAlignment = pylon.OutputBitAlignment_MsbAligned

contador_fotos = 0

try:
    while True:
        if arduino.in_waiting > 0:
            linea = arduino.readline().decode('utf-8').strip()
            print(f"Mensaje recibido: {linea}")

            if linea == "capturar":
                print("📸 Capturando foto...")

                grabResult = camera.RetrieveResult(5000, pylon.TimeoutHandling_ThrowException)

                if grabResult.GrabSucceeded():
                    image = converter.Convert(grabResult)
                    img = image.GetArray()

                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    filename = os.path.join(output_folder, f'foto_{timestamp}.jpg')
                    cv2.imwrite(filename, img)

                    contador_fotos += 1
                    print(f"✅ Foto guardada: {filename} (Total fotos: {contador_fotos})")

                grabResult.Release()

except KeyboardInterrupt:
    print("🛑 Programa detenido manualmente")

finally:
    camera.StopGrabbing()   #Paramos la captura continua
    camera.Close()
    arduino.close()
    print("🔒 Recursos liberados correctamente")
