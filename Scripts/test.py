import RPi.GPIO as GPIO
import time
import board
import adafruit_dht
import serial
import adafruit_gps
from datetime import datetime
import math

# Configuración del sensor DHT22
dhtDevice = adafruit_dht.DHT22(board.D22)

# Configuración del sensor ultrasónico SRF05
GPIO.setmode(GPIO.BCM)
TRIG = 23  # Pin GPIO para TRIG del sensor ultrasónico
ECHO = 24  # Pin GPIO para ECHO del sensor ultrasónico
GPIO.setup(TRIG, GPIO.OUT)
GPIO.setup(ECHO, GPIO.IN)

# Configuración del GPS (usando la interfaz serial)
uart = serial.Serial("/dev/serial0", baudrate=9600, timeout=10)
gps = adafruit_gps.GPS(uart, debug=False)
gps.send_command(b"PMTK220,1000*1F")  # Actualización cada segundo

# Datos del tanque
H = 20.0  # Altura total del tanque en cm
r = 8.0  # Radio de la base del tanque en cm
A = math.pi * (r ** 2)  # Área de la base del tanque
V = A * H / 1000  # Volumen total del tanque en litros

# Función para medir distancia con el sensor ultrasónico
def medir_distancia():
    GPIO.output(TRIG, False)
    time.sleep(2)
    GPIO.output(TRIG, True)
    time.sleep(0.00001)
    GPIO.output(TRIG, False)
    while GPIO.input(ECHO) == 0:
        inicio_pulso = time.time()
    while GPIO.input(ECHO) == 1:
        final_pulso = time.time()
    duracion_pulso = final_pulso - inicio_pulso
    distancia = duracion_pulso * 17150
    distancia = round(distancia, 2)
    return distancia

# Función para calcular el volumen de agua actual en el tanque
def calcular_volumen(distancia):
    h_agua = H - distancia  # Altura del agua en cm
    V_actual = A * h_agua / 1000  # Volumen actual en litros
    return V_actual

# Función para calcular el porcentaje de llenado del tanque
def calcular_porcentaje(V_actual):
    porcentaje_lleno = (V_actual / V) * 100
    return round(porcentaje_lleno, 2)

# Archivo donde se guardarán los datos
archivo = "datos_sensores.txt"

try:
    while True:
        # Obtener la fecha y hora actual
        fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Leer el sensor DHT22
        temperatura = dhtDevice.temperature
        humedad = dhtDevice.humidity
        #print(f"{temperatura}\n")

        # Leer el sensor ultrasónico
        distancia = medir_distancia()
        V_actual = calcular_volumen(distancia)
        porcentaje_lleno = calcular_porcentaje(V_actual)

        # Leer datos del GPS
        gps.update()
        
        if gps.has_fix:
            print("Leyendo...\n")
            latitud = gps.latitude
            longitud = gps.longitude
            altitud = gps.altitude_m
        else:
            latitud = longitud = altitud = "Sin señal"
            print(latitud)
        
        # Escribir los datos en el archivo
        if latitud != "Sin señal":
            
            with open(archivo, "a") as file:
                print("Dato leído:\n")
                print(f"Temperatura: {temperatura:.2f}°C, \n")
                print(f"Humedad: {humedad:.2f}%\n")
                print(f"Latitud: {latitud},")
                print(f"Longitud: {longitud},")
                print(f"Altitud: {altitud}\n")
                print(f"Distancia: {distancia} cm\n")
                file.write(f"{fecha_hora}, ")
                file.write(f"Temperatura: {temperatura:.2f}°C, ")
                file.write(f"Humedad: {humedad:.2f}%, ")
                file.write(f"Latitud: {latitud}, ")
                file.write(f"Longitud: {longitud}, ")
                file.write(f"Altitud: {altitud}, ")
                file.write(f"Distancia: {distancia} cm, ")
                file.write(f"Porcentaje de llenado: {porcentaje_lleno:.2f}%\n")

        # Esperar antes de la próxima lectura
        time.sleep(8)

except KeyboardInterrupt:
    print("Programa detenido por el usuario")
finally:
    GPIO.cleanup()
