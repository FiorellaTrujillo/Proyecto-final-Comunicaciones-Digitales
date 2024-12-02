import usys
import ustruct as struct
import utime
from machine import Pin, SPI
from nrf24l01 import NRF24L01
from micropython import const

# Nueva configuración de pines
cfg = {"spi": 0, "miso": 4, "mosi": 7, "sck": 6, "csn": 9, "ce": 10}

# Inicialización del SPI y NRF24L01
spi = SPI(cfg["spi"], baudrate=10000000, polarity=0, phase=0, sck=Pin(cfg["sck"]), mosi=Pin(cfg["mosi"]), miso=Pin(cfg["miso"]))
nrf = NRF24L01(spi, Pin(cfg["csn"]), Pin(cfg["ce"]), payload_size=32)
nrf.open_tx_pipe(b"\xe1\xf0\xf0\xf0\xf0")
nrf.open_rx_pipe(1, b"\xd2\xf0\xf0\xf0\xf0")
nrf.start_listening()

# Leer la imagen en blanco y negro
with open('imagen_comprimida6.jpg', 'rb') as f:
    image_data = f.read()

# Dividir la imagen en paquetes de 32 bytes
packets = [image_data[i:i+32] for i in range(0, len(image_data), 32)]

# Enviar los paquetes
for packet in packets:
    nrf.stop_listening()
    try:
        nrf.send(packet)
        print("Paquete enviado")
        # Esperar confirmación de recepción
        nrf.start_listening()
        start_time = utime.ticks_ms()
        while not nrf.any():
            if utime.ticks_diff(utime.ticks_ms(), start_time) > 1000:  # Timeout de 1000 ms
                print("Timeout esperando confirmación")
                break
        if nrf.any():
            ack = nrf.recv()
            print("Confirmación recibida:", ack)
    except OSError:
        print("Error al enviar el paquete")
    utime.sleep(0.01)