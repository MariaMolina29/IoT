import paho.mqtt.publish as publish
import time

# Configuración de MQTT para ThingSpeak
mqtt_client_ID = "KQURJjcKHwUKFzodEhADDQQ"
mqtt_username = "KQURJjcKHwUKFzodEhADDQQ"
mqtt_password = "UFfOYXaeGhxQ69V1OlnC2rmY"
channel_id = "2679274"  # Cambia esto por el ID de tu canal
mqtt_host = "mqtt3.thingspeak.com"
topic = f"channels/{channel_id}/publish"

# Función para enviar datos a ThingSpeak
def enviar_datos_thingspeak(field, valor, id_sensor, timestamp, unidad):
    try:
        # Crear el payload con los datos numéricos y metadatos
        payload = f"{field}={valor}&status=[ID sensor: {id_sensor}] [timestamp: {timestamp}] [Unidad: {unidad}]"

        # Enviar el payload a ThingSpeak
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
        print(f"Datos enviados a ThingSpeak: {payload}")

    except Exception as e:
        print(f"Error al enviar datos a ThingSpeak: {e}")

# Leer el archivo datos_limpios.txt y enviar los datos
with open('datos_limpios.txt', 'r', encoding='utf-8', errors='ignore') as file:
    for line in file:
        try:
            # Dividir la línea por comas
            datos = line.strip().split(",")

            # Extraer cada valor de la línea
            timestamp = datos[0]
            temperatura = float(datos[1])
            humedad = float(datos[2])
            latitud = float(datos[3])
            longitud = float(datos[4])
            altitud = float(datos[5])  # Altitud desde la línea
            porcentaje_llenado = float(datos[6])  # Porcentaje de llenado desde la línea

            # Mensaje de depuración para verificar la extracción
            print(f"Línea procesada: {timestamp}, {temperatura}°C, {humedad}%, {latitud}, {longitud}, {altitud}m, Porcentaje: {porcentaje_llenado}%")

            # Enviar datos a ThingSpeak para cada variable con su respectivo formato
            # Enviar Temperatura
            enviar_datos_thingspeak("field1", temperatura, "DHT22", timestamp,"Celsius")
            

            # Enviar Humedad
            enviar_datos_thingspeak("field2", humedad, "DHT22", timestamp,"Percentage")

            # Enviar Latitud
            enviar_datos_thingspeak("field3", latitud, "GPS", timestamp, "Degrees")

            # Enviar Longitud
            enviar_datos_thingspeak("field4", longitud, "GPS", timestamp,"Degrees")

            # Enviar Altitud
            if (altitud == 'None'):
                enviar_datos_thingspeak("field5", 0, "GPS", timestamp,"Meters")
            else:
                enviar_datos_thingspeak("field5", altitud, "GPS", timestamp,"Meters")


            # Enviar Porcentaje de Llenado
            enviar_datos_thingspeak("field6", porcentaje_llenado, "Ultrasonic", timestamp,"Percentage")

        except Exception as e:
            print(f"Error procesando la línea: {line.strip()} - {e}")
