import asyncio
import json
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder

class VideoServerProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.server_address = None  # Dirección del servidor de señalización
        self.clients = {}  # Diccionario para manejar múltiples clientes (por dirección)

    def connection_made(self, transport):
        self.transport = transport
        print("Conexión con el servidor de señalización establecida.")

        # Enviar mensaje de registro al servidor de señalización
        register_message = {"type": "REGISTER"}
        self.transport.sendto(json.dumps(register_message).encode(), self.server_address)
        print("Servidor de video registrado en el servidor de señalización.")

    def datagram_received(self, data, addr):
        asyncio.create_task(self.handle_message(data, addr))

    async def handle_message(self, data, addr):
        try:
            message = json.loads(data.decode())

            message_type = message.get("type")

            if message_type == "offer":
                print(f"Oferta recibida del cliente {addr}. Procesando...")
                await self.handle_offer(message, addr)

            elif message_type == "bye":
                print(f"Mensaje 'bye' recibido del cliente {addr}. Desconectando...")
                await self.handle_bye(addr)

        except json.JSONDecodeError:
            print(f"Error al decodificar mensaje desde {addr}: {data.decode()}")

    async def handle_offer(self, message, addr):
        # Crear nuevas instancias de RTCPeerConnection y MediaRecorder para cada cliente
        pc = RTCPeerConnection()
        recorder = MediaRecorder(f"video-{addr[1]}.mp4")

        @pc.on("track")
        def on_track(track):
            print(f"Grabando video del cliente {addr}")
            recorder.addTrack(track)

        # Configurar conexión WebRTC con el cliente
        offer = RTCSessionDescription(message["sdp"], message["type"])
        await pc.setRemoteDescription(offer)

        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        # Guardar el cliente activo
        self.clients[addr] = (pc, recorder)

        # Enviar respuesta al cliente
        answer_message = {"type": "answer", "sdp": pc.localDescription.sdp}
        self.transport.sendto(json.dumps(answer_message).encode(), addr)

        print(f"Respuesta enviada al cliente {addr}.")

    async def handle_bye(self, addr):
        if addr in self.clients:
            pc, recorder = self.clients.pop(addr)

            await pc.close()
            await recorder.stop()

            print(f"Cliente {addr} desconectado y grabación finalizada.")

    def error_received(self, exc):
        print(f"Error recibido: {exc}")

async def main():
    signalling_host = "127.0.0.1"
    signalling_port = 9999

    loop = asyncio.get_event_loop()

    # Configurar el transporte y el protocolo para el servidor de video
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: VideoServerProtocol(),
        remote_addr=(signalling_host, signalling_port),
        local_addr=("0.0.0.0", 12346)  # Puerto donde el servidor escucha
    )

    try:
        while True:
            await asyncio.sleep(3600)  # Mantener el servidor activo
    except KeyboardInterrupt:
        print("\nServidor de video detenido manualmente.")

if __name__ == "__main__":
    asyncio.run(main())
