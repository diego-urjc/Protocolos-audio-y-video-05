import asyncio
import json
import sys

from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaBlackhole, MediaPlayer, MediaRecorder


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
    terminado = False

    # Crea una peer connection (conexión WebRTC)
    pc = RTCPeerConnection()

    recorder = MediaRecorder("video-out.mp4")

    @pc.on("track")
    def on_track(track):
        print("Recibiendo video")
        recorder.addTrack(track)

    # Crea un lector de la entrada estandard, para poder leer lo que
    # escriba el usuario
    reader = await input_reader(bucle)
    # Pide al usuario que pegue el mensaje del cliente
    print("-- Pega el mensaje del cliente (recepción de señalización) --")

    while not terminado:
        # Lee el mensaje de señalización del cliente, y conviértela en un diccionario
        mensaje_str = await reader.readline()
        mensaje = json.loads(mensaje_str)

        if mensaje["type"] == "offer":
            oferta = RTCSessionDescription(mensaje["sdp"], mensaje["type"])
            await pc.setRemoteDescription(oferta)
            await recorder.start()

            # Crea una configuración para la parte local de la peer connection
            # (conexión WebRTC)
            config = await pc.createAnswer()
            # Configura la parte local de la peer connection (conexión WebRTC)
            await pc.setLocalDescription(config)
            # Obtén un documento SDP con los datos de la parte local
            # de la conexión WebRTC
            sdp = pc.localDescription.sdp
            # Crea un diccionario que sirva de respuesta, y conviértelo en un
            # documento (string) en formato JSON
            respuesta = {"type": "answer", "sdp": sdp}
            respuesta_str = json.dumps(respuesta)

            # Pide al usuario que copie la respuesta al cliente
            print("-- Copia esta respuesta en el cliente (envío de señalización) --", flush=True)
            print(respuesta_str)

        elif mensaje["type"] == "bye":
            print("Terminando...")
            terminado = True
    pc.close()


# comentario para poder hacer commit de nuevo
if __name__ == "__main__":
    asyncio.run(main())
