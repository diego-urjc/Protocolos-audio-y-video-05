#!/usr/bin/env python3

""" Cliente WebRTC sencillo

Crea una peer connection (conexión WebRTC), usa como señalización
(para enviar la oferta y la respuesta) al usuario, que copia y pega
la oferta (y luego la respuesta) SDP, y cuando la peer connection
(y su canal de video) está establecida, envía el vídeo video.webm.
"""

import asyncio
import json
import sys

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer

async def input_reader(bucle):
    """Crea un lector de la entrada estándar

    Este lector se puede usar dentro del bucle de eventos, donde
    debido a la asincronía, el `input`normal no funciona."""

    lector = asyncio.StreamReader(loop=bucle)
    read_transport, _ = await bucle.connect_read_pipe(
        lambda: asyncio.StreamReaderProtocol(lector), sys.stdin
    )
    return lector


async def main():
    """Código princial"""

    # Consigue una referencia al bucle de eventos
    bucle = asyncio.get_event_loop()
    # Crea un futuro para indicar cuando hemos terminado
    terminado = bucle.create_future()

    # Crea una peer connection (conexión WebRTC)
    pc = RTCPeerConnection()

    # Añade un canal (track) de video
    player = MediaPlayer("video.webm")
    pc.addTrack(player.video)
    print(f"Creado el canal de video.")

    # Crea una configuración para la parte local de la peer connection
    # (conexión WebRTC)
    config = await pc.createOffer()
    # Configura la parte local de la peer connection (conexión WebRTC)
    await pc.setLocalDescription(config)
    # Obtén un documento SDP con los datos de la parte local
    # de la conexión WebRTC
    sdp = pc.localDescription.sdp
    # Crea un diccionario que sirva de oferta, y conviértelo en un
    # documento (string) en formato JSON
    oferta = {"type": "offer", "sdp": sdp}
    oferta_str = json.dumps(oferta)

    # Pide al usuario que copie la oferta al servidor
    print("-- Copia esta oferta en el servidor (envío de señalización) --", flush=True)
    print(oferta_str)

    # Crea un lector de la entrada estandard, para poder leer lo que
    # escriba el usuario
    reader = await input_reader(bucle)
    # Pide al usuario que pegue la respuesta del servidor
    print("-- Pega la respuesta del servidor (recepción de señalización) --")

    # Lee la respuesta del servidor, y conviértela en un diccionario
    mensaje_str = await reader.readline()
    mensaje = json.loads(mensaje_str)
    if mensaje["type"] == "answer":
        # Si lo que ha pegado el usuario es una respuesta, crea
        # un objeto RTCSessionDescription con esos datos
        respuesta = RTCSessionDescription(mensaje["sdp"], mensaje["type"])
        # Configura la parte remota de la peer connection (conexión WebRTC)
        await pc.setRemoteDescription(respuesta)
        print("-- Conexión establecida --")
    else:
        # Si lo que ha pegado el usuario no es una respuesta, termina
        exit("El mensaje de señalización no era una respuesta.")

    def on_ended():
        """Manejador del evento "ended" para el canal (track) de video"""
        print("Canal de video terminado.")
        # Resuelve (da valor) el futuro terminado
        terminado.set_result(True)

    # Pon el manejador para el evento "ended" del canal (track) de video
    player.video.add_listener("ended", on_ended)

    # Espera en el futuro terminado (hasta que el manejador anterior se active)
    await terminado
    print("Terminado")

    print("-- Copia esta despedida en el servidor (envío de señalización) --", flush=True)
    print("{ \"type\": \"bye\" }")
    # Cierra la peer connection para terminar
    await pc.close()
    #comentario para poder hacer commit

if __name__ == "__main__":
    asyncio.run(main())
