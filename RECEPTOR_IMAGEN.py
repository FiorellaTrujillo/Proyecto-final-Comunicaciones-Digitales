import sys
import usys
import ustruct as struct
import utime
import network
import urequests
from machine import Pin, SPI
from nrf24l01 import NRF24L01
from micropython import const

# Configuración red de internet
ssid = 'HOLA'
password = '11111111'

wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(ssid, password)

# Configuración de pines
cfg = {"spi": 1, "miso": 8, "mosi": 11, "sck": 10, "csn": 14, "ce": 17}

# Inicialización del SPI y NRF24L01
spi = SPI(cfg["spi"])
nrf = NRF24L01(spi, Pin(cfg["csn"]), Pin(cfg["ce"]), payload_size=32)
nrf.open_tx_pipe(b"\xe1\xf0\xf0\xf0\xf0")
nrf.open_rx_pipe(1, b"\xd2\xf0\xf0\xf0\xf0")
nrf.start_listening()

while not wlan.isconnected():
    utime.sleep(1)

print('Connected to WiFi')

def receive_image():
    image_data = bytearray()
    timeout = 5  # Tiempo de espera en segundos
    last_received = utime.time()

    while True:
        if nrf.any():
            packet = nrf.recv()
            image_data.extend(packet)
            print("Paquete recibido, tamaño actual de image_data:", len(image_data))
            
            # Enviar confirmación de recepción
            nrf.stop_listening()
            try:
                nrf.send(b'ACK')
                print("Confirmación enviada")
            except OSError:
                print("Error al enviar la confirmación")
            nrf.start_listening()
            last_received = utime.time()  # Reiniciar el temporizador
        else:
            if utime.time() - last_received > timeout:
                print("Tiempo de espera agotado, terminando la recepción.")
                break

        utime.sleep(0.1)

    # Verificar el tamaño de los datos recibidos
    if len(image_data) > 0:
        print(f"Total de datos recibidos: {len(image_data)} bytes")

        # Guardar los datos de la imagen en un archivo .byn
        with open('image_data.byn', 'wb') as f:
            f.write(image_data)

        print("Datos de la imagen guardados en 'image_data.byn'.")
        return 'image_data.byn'
    else:
        print("No se recibieron datos de imagen.")
        return None

def send_image_to_server(image_path):
    url = 'http://192.168.1.12:5000/upload'  # Reemplaza con la IP de tu servidor
    headers = {'Content-Type': 'application/octet-stream'}

    # Abrir el archivo .byn y enviarlo al servidor
    with open(image_path, 'rb') as f:
        data = f.read()
        response = urequests.post(url, data=data, headers=headers, timeout=10)

    print("Respuesta del servidor:", response.text)

while True:
    print("Esperando recibir una nueva imagen...")
    image_path = receive_image()
    if image_path:
        print("Enviando imagen al servidor...")
        send_image_to_server(image_path)
    else:
        print("No se recibió ninguna imagen válida.")
    
