import asyncio
import json
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder


class VideoServerProtocol(asyncio.DatagramProtocol):
    def __init__(self, on_ready):
        self.on_ready = on_ready
        self.server_address = None  # Dirección del servidor de señalización
        self.clients = {}  # Diccionario para manejar múltiples clientes

    def connection_made(self, transport):
        self.transport = transport
        print("Conexión con el servidor de señalización establecida.")

        # Enviar mensaje de registro
        register_message = {"type": "REGISTER"}
        self.transport.sendto(json.dumps(register_message).encode(), self.server_address)
        print("Registrado en el servidor de señalización.")

    def datagram_received(self, data, addr):
        message = json.loads(data.decode())
        if message["type"] == "offer":
            print(f"Oferta recibida del cliente {addr}. Procesando...")
            asyncio.create_task(self.handle_offer(message, addr))

        elif message["type"] == "bye":
            print(f"Mensaje 'bye' recibido del cliente {addr}. Finalizando grabación...")
            self.clients.pop(addr, None)  # Eliminar cliente de la lista
            print("Esperando nuevas ofertas...")

    async def handle_offer(self, message, addr):
        # Crear nueva instancia de RTCPeerConnection y MediaRecorder para cada cliente
        pc = RTCPeerConnection()
        recorder = MediaRecorder("video-out.mp4")  # Guardar video con puerto único del cliente

        @pc.on("track")
        async def on_track(track):
            print(f"Recibiendo video del cliente {addr}...")
            recorder.addTrack(track)
            print("Track añadido al recorder")
            await recorder.start()
            print("Grabación iniciada")

            @track.on("ended")
            async def on_ended():
                print(f"Track terminado para el cliente {addr}. Deteniendo grabación...")
                await recorder.stop()  # Detener la grabación y finalizar el archivo
                print(f"Grabación finalizada y guardada como 'video-out.mp4'.")

        # Configurar conexión WebRTC
        offer = RTCSessionDescription(message["sdp"], message["type"])
        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        # Guardar cliente activo
        self.clients[addr] = (pc, recorder)

        # Enviar respuesta al cliente
        answer_message = {"type": "answer", "sdp": pc.localDescription.sdp}
        self.transport.sendto(json.dumps(answer_message).encode(), self.server_address)
        print(f"Respuesta enviada al cliente {addr}.")

    def error_received(self, exc):
        print(f"Error recibido: {exc}")


async def main():
    signalling_host = "127.0.0.1"
    signalling_port = 9999

    # Crear el futuro para manejar el protocolo
    ready_future = asyncio.Future()

    # Crear transporte UDP con protocolo de servidor de video
    loop = asyncio.get_event_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: VideoServerProtocol(ready_future),
        remote_addr=(signalling_host, signalling_port),
        local_addr=("0.0.0.0", 12345),  # Puerto fijo donde escucha este servidor
    )

    # Mantener el servidor activo
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("Servidor detenido manualmente.")


if __name__ == "__main__":
    asyncio.run(main())
