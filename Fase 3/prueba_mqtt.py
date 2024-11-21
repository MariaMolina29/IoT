import time
import board
import adafruit_dht
import serial
import adafruit_gps
import requests
from datetime import datetime
import paho.mqtt.publish as publish
import RPi.GPIO as GPIO

# Configuración del sensor DHT22
dhtDevice = adafruit_dht.DHT22(board.D27)

# Configuración del GPS (usando la interfaz serial)
uart = serial.Serial("/dev/serial0", baudrate=9600, timeout=10)
gps = adafruit_gps.GPS(uart, debug=False)
gps.send_command(b"PMTK220,1000*1F")  # Actualización cada segundo

# Configuración del pin GPIO
#GPIO.setmode(GPIO.BCM)  # Usar numeración BCM
#GPIO_RELAY = 26  # Pin GPIO que controla el relé
# Configurar el pin como salida
GPIO.setup(16, GPIO.OUT,initial=GPIO.LOW)



# Datos del tanque
H = 6.76  # Altura total del tanque en cm
A = 20*14  # Área de la base del tanque
V = A * H / 1000  # Volumen total del tanque en litros



# Configuración para la API de clima
API_KEY = "70ef849c85487983236305fde6792add"
weather_url = "http://api.openweathermap.org/data/2.5/weather"

# Configuración de MQTT para ThingSpeak
mqtt_client_ID = "KQURJjcKHwUKFzodEhADDQQ"
mqtt_username = "KQURJjcKHwUKFzodEhADDQQ"
mqtt_password = "UFfOYXaeGhxQ69V1OlnC2rmY"
channel_id = "2679274"  # ID del canal
mqtt_host = "mqtt3.thingspeak.com"
topic = f"channels/{channel_id}/publish"

# Umbrales para evaluar el riesgo de helada
UMBRAL_TEMP = 20  # Grados Celsius
UMBRAL_HUMEDAD = 50  # Porcentaje de humedad
UMBRAL_VIENTO_CALMA = 6  # Velocidad del viento en m/s

# Función para medir distancia con el sensor ultrasónico
def medir_distancia():
    try:
        # Configuración del sensor ultrasónico SRF05
        GPIO.setmode(GPIO.BCM)
        TRIG = 23  # Pin GPIO para TRIG del sensor ultrasónico
        ECHO = 24  # Pin GPIO para ECHO del sensor ultrasónico
        GPIO.setup(TRIG, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(ECHO, GPIO.IN)
        #inicio_pulso = 0
        #final_pulso = 0
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
    except KeyboardInterrupt:
        print("Programa detenido por el usuario.")
    finally:
        # Limpieza de los pines GPIO
        GPIO.cleanup()

# Función para calcular el volumen de agua actual en el tanque
def calcular_volumen(distancia):
    print(distancia)
    h_agua = H - distancia  # Altura del agua en cm
    V_actual = A * h_agua / 1000  # Volumen actual en litros
    return V_actual

# Función para calcular el porcentaje de llenado del tanque
def calcular_porcentaje(V_actual):
    porcentaje_lleno = (V_actual / V) * 100
    return round(porcentaje_lleno, 2)
    
# Función para calcular el punto de rocío
def calcular_punto_rocio(temp, humedad):
    """Calcula el punto de rocío aproximado."""
    return temp - ((100 - humedad) / 5)

# Función para evaluar el riesgo de helada
def evaluar_riesgo_helada(temp, humedad, velocidad_viento, porcentaje_llenado):
    GPIO_RELAY = 16  # Pin GPIO que controla el relé
    # Configurar el pin como salida
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_RELAY, GPIO.OUT, initial=GPIO.LOW)
    
    """Evalúa el riesgo de helada basado en temperatura, humedad y viento."""
    #punto_rocio = calcular_punto_rocio(temp, humedad)
    riesgo = temp <= UMBRAL_TEMP and humedad >= UMBRAL_HUMEDAD
    calma = velocidad_viento < UMBRAL_VIENTO_CALMA
    lleno = porcentaje_llenado > 5
    
    prob=calcular_probabilidad(temp, humedad, velocidad_viento)
    print(f"Proba: {prob}%")

    if riesgo and calma and lleno:
        print(f" Riesgo de helada detectado! Temp = {temp:.2f} °C, Humedad = {humedad:.2f} % ")
        
        # Activar la bomba de agua
        print("Encendiendo la bomba de agua...\n")
        GPIO.output(GPIO_RELAY, GPIO.HIGH)  # Cambia a GPIO.LOW si el relé está inversamente conectado
        time.sleep(4)  # Mantener la bomba encendida por 4 segundos

        # Desactivar la bomba de agua
        print("Apagando la bomba de agua...\n")
        GPIO.output(GPIO_RELAY, GPIO.LOW)  # Cambia a GPIO.HIGH si el relé está inversamente conectado
        enviar_datos_thingspeak("field8", prob, "Activación", fecha_hora, "Percentage")
        time.sleep(2)
        
        
    elif riesgo and calma and not lleno:
        print(" No hay suficiente agua\n")
        enviar_datos_thingspeak("field8", prob, "No Activación", fecha_hora, "Percentage")
    elif not riesgo and not calma and lleno:
        print(" No se detecta riesgo de helada.\n")
        enviar_datos_thingspeak("field8", prob, "No Activación", fecha_hora, "Percentage")
        
        
        
    
       
    
    GPIO.cleanup()

def calcular_probabilidad(temp, hum, vel):
    proba =0
    
    if temp<=0:
        proba +=50
    elif 0<temp<=5:
        proba +=(5-temp)*10
        
    if hum >=80:
        proba +=20
    elif 60 <=hum<80:
        probabilidad +=10
    
    if vel <2:
        proba+= 20
    elif 2<= vel <=6:
        proba += 10
    
    proba = max(0, min(100,proba))
    
    return proba
        
# Función para obtener el clima externo
def obtener_clima_externo(lat, lon):
    try:
        params = {
            'lat': lat,
            'lon': lon,
            'appid': API_KEY,
            'units': 'metric'
        }
        response = requests.get(weather_url, params=params)
        data = response.json()
        temp_externa = data['main']['temp']
        humedad_externa = data['main']['humidity']
        velocidad_viento = data['wind']['speed']
        return temp_externa, humedad_externa, velocidad_viento
    except Exception as e:
        print(f"Error al obtener datos del clima externo: {e}")
        return None, None, None

# Función para enviar datos a ThingSpeak
def enviar_datos_thingspeak(field, valor, id_sensor, timestamp, unidad):
    try:
        # Crear el payload con los datos numéricos y metadatos
        payload = f"{field}={valor}&status=[ID sensor: {id_sensor}] [timestamp: {timestamp}] [Unidad: {unidad}]"
        publish.single(
            topic,
            payload=payload,
            hostname=mqtt_host,
            transport="tcp",
            port=1883,
            client_id=mqtt_client_ID,
            auth={
                'username': mqtt_username,
                'password': mqtt_password,
            }
        )
        time.sleep(2)
        print(f"Datos enviados a ThingSpeak: {payload}\n")
    except Exception as e:
        print(f"Error al enviar datos a ThingSpeak: {e}")

try:
    while True:
        # Obtener timestamp actual
        fecha_hora = datetime.now().isoformat()
        
        # Leer el sensor ultrasónico
        distancia = medir_distancia()
        V_actual = calcular_volumen(distancia)
        porcentaje_lleno = calcular_porcentaje(V_actual)
        if porcentaje_lleno< 0:
            porcentaje_lleno = 0
        print(porcentaje_lleno)
            
        # Leer datos del sensor DHT22
        try:
            temperatura_local = dhtDevice.temperature
            humedad_local = dhtDevice.humidity
            
            print(f"Temperatura local: {temperatura_local} °C, Humedad local: {humedad_local} %, Porcentaje: {porcentaje_lleno} %\n")
        except RuntimeError as e:
            print(f"Error al leer DHT22: {e}")
            temperatura_local, humedad_local = None, None
            temperatura_local, humedad_local = None, None

        # Leer datos del GPS
        #gps.update()
        #if gps.has_fix:
        latitud = 4.626685
        longitud = -74.06452
        print(f"Coordenadas GPS: Latitud = {latitud}, Longitud = {longitud}\n")

        # Obtener datos meteorológicos externos
        temp_externa, humedad_externa, velocidad_viento = obtener_clima_externo(latitud, longitud)
        if temp_externa is not None and humedad_externa is not None:
            print(f"Clima externo: Temp = {temp_externa} °C, Humedad = {humedad_externa} %, Vel. viento = {velocidad_viento} m/s\n")
            # Evaluar el riesgo de helada con datos externos
            #evaluar_riesgo_helada(temp_externa, humedad_externa, velocidad_viento)
            # Crear el payload para ThingSpeak
            # Enviar datos a ThingSpeak
            enviar_datos_thingspeak("field1", temperatura_local, "DHT22", fecha_hora, "Celsius")
            enviar_datos_thingspeak("field2", humedad_local, "DHT22", fecha_hora, "Percentage")
            enviar_datos_thingspeak("field3", latitud, "GPS", fecha_hora, "Degrees")
            enviar_datos_thingspeak("field4", humedad_externa, "GPS", fecha_hora, "Percentage")
            enviar_datos_thingspeak("field5", porcentaje_lleno, "Ultrasonic", fecha_hora, "Percentage")
            enviar_datos_thingspeak("field6", velocidad_viento, "GPS",fecha_hora,"Meters per second" )
            enviar_datos_thingspeak("field7", temp_externa, "GPS", fecha_hora, "Celsius")
                
        else:
            temp_externa,humedad_externa, velocidad_viento = None, None, None
            print("Esperando señal GPS...\n")
            
            
            # Crear el payload para ThingSpeak
            # Enviar datos a ThingSpeak
            enviar_datos_thingspeak("field1", temperatura_local, "DHT22", fecha_hora, "Celsius")
            enviar_datos_thingspeak("field2", humedad_local, "DHT22", fecha_hora, "Percentage")
            enviar_datos_thingspeak("field3", 0, "GPS", fecha_hora, "Degrees")
            enviar_datos_thingspeak("field4", 0, "GPS", fecha_hora, "Degrees")
            enviar_datos_thingspeak("field5", porcentaje_lleno, "Ultrasonic", fecha_hora, "Percentage")
            enviar_datos_thingspeak("field6", 0, "GPS",fecha_hora,"Meters per second" )
            enviar_datos_thingspeak("field7", 0, "GPS", fecha_hora, "Celsius")
            
        

        # Evaluar el riesgo de helada con datos locales si están disponibles
      
        if temp_externa is not None and temperatura_local is not None and humedad_externa is not None and humedad_local is not None:
            if temperatura_local < temp_externa and humedad_local > humedad_externa:
                evaluar_riesgo_helada(temperatura_local, humedad_local, velocidad_viento, porcentaje_lleno)
            elif temperatura_local > temp_externa and humedad_local < humedad_externa:
                evaluar_riesgo_helada(temp_externa, humedad_externa, velocidad_viento, porcentaje_lleno)
        elif temperatura_local is None and temp_externa is not None:
            evaluar_riesgo_helada(temp_externa, humedad_externa, velocidad_viento, porcentaje_lleno)
        
        # Esperar antes de la próxima iteración
        time.sleep(30)

except KeyboardInterrupt:
    print("Programa detenido por el usuario.")
finally:
    print("Limpieza finalizada.")
