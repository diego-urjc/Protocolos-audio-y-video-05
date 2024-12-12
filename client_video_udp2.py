import asyncio
import json
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer


class ClientProtocol(asyncio.DatagramProtocol):
    def __init__(self, pc, offer, video_done_future):
        self.pc = pc
        self.offer = offer
        self.video_done_future = video_done_future
        self.server_address = None

    def connection_made(self, transport):
        self.transport = transport
        print("Conexión con el servidor de señalización establecida.")

        # Enviar oferta al servidor de señalización
        self.transport.sendto(json.dumps(self.offer).encode(), self.server_address)
        print("Enviada oferta al servidor de señalización.")

    def datagram_received(self, data, addr):
        """Se llama cuando se recibe un mensaje del servidor de señalización."""
        message = json.loads(data.decode())
        if message["type"] == "answer":
            print("Respuesta recibida del servidor de video. Procesando...")
            asyncio.create_task(self.handle_answer(message))

    async def handle_answer(self, message):
        answer = RTCSessionDescription(message["sdp"], message["type"])
        await self.pc.setRemoteDescription(answer)
        print("-- Conexión establecida con el servidor de video --")

    def send_bye(self):
        # Enviar mensaje "bye" al servidor
        bye_message = {"type": "bye"}
        self.transport.sendto(json.dumps(bye_message).encode(), self.server_address)
        print("-- Enviado mensaje 'bye' --")
        self.video_done_future.set_result(True)

    def error_received(self, exc):
        print(f"Error recibido: {exc}")

    def connection_lost(self, exc):
        print("Conexión perdida con el servidor de señalización.")


async def main():
    signalling_host = "127.0.0.1"
    signalling_port = 9999

    # Configuración de WebRTC
    pc = RTCPeerConnection()
    player = MediaPlayer("video.webm")
    pc.addTrack(player.video)
    video_done_future = asyncio.Future()

    # Crear oferta SDP
    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)
    offer_message = {"type": "offer", "sdp": pc.localDescription.sdp}

    # Crear transporte UDP con protocolo de cliente
    loop = asyncio.get_event_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: ClientProtocol(pc, offer_message, video_done_future),
        remote_addr=(signalling_host, signalling_port),
        local_addr=("0.0.0.0", 54321),  # Puerto fijo donde escucha este cliente
    )

    # Configurar evento "ended" para saber cuándo termina el video
    @player.video.on("ended")
    def on_video_end():
        protocol.send_bye()

    # Esperar hasta que el video termine de enviarse
    await video_done_future

    # Cerrar el canal de video y la conexión WebRTC
    print("Cerrando conexion...")
    await pc.close()
#comentario para hacer commit


if __name__ == "__main__":
    asyncio.run(main())
