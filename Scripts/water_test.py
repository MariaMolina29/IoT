import RPi.GPIO as GPIO
import time

# Configuración del pin GPIO
GPIO.setmode(GPIO.BCM)  # Usar numeración BCM
GPIO_RELAY = 17  # Pin GPIO que controla el relé

# Configurar el pin como salida
GPIO.setup(GPIO_RELAY, GPIO.OUT)

try:
    # Activar la bomba de agua
    print("Encendiendo la bomba de agua...")
    GPIO.output(GPIO_RELAY, GPIO.HIGH)  # Cambia a GPIO.LOW si el relé está inversamente conectado
    time.sleep(2)  # Mantener la bomba encendida por 4 segundos

    # Desactivar la bomba de agua
    print("Apagando la bomba de agua...")
    GPIO.output(GPIO_RELAY, GPIO.LOW)  # Cambia a GPIO.HIGH si el relé está inversamente conectado
    time.sleep(2)

except KeyboardInterrupt:
    print("Programa detenido por el usuario.")

finally:
    # Limpieza de los pines GPIO
    GPIO.cleanup()
