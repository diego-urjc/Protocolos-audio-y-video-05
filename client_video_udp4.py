import asyncio
import json
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaPlayer
import random


class ClientProtocol(asyncio.DatagramProtocol):
    def __init__(self, offer, video_done_future):
        self.offer = offer  # Oferta inicializada en el constructor
        self.video_done_future = video_done_future
        self.server_address = None
        self.connection = None

    def connection_made(self, transport):
        self.transport = transport
        print("Conexión con el servidor de señalización establecida.")
        self.transport.sendto(json.dumps(self.offer).encode(), self.server_address)
        print("Enviada oferta al servidor de señalización.")

    def datagram_received(self, data, addr):
        message = json.loads(data.decode())
        if message["type"] == "answer":
            print(f"Respuesta recibida del servidor de video. Procesando...")
            asyncio.create_task(self.handle_answer(message))

    async def handle_answer(self, message):
        answer = RTCSessionDescription(message["sdp"], message["type"])
        await self.connection.setRemoteDescription(answer)
        print("-- Conexión establecida con el servidor de video --")

    def send_bye(self):
        bye_message = {"type": "bye"}
        self.transport.sendto(json.dumps(bye_message).encode(), self.server_address)
        print("-- Enviado mensaje 'bye' --")
        self.video_done_future.set_result(True)

    def connection_lost(self, exc):
        print("Conexión perdida con el servidor de señalización.")


async def main():
    signalling_host = "127.0.0.1"
    signalling_port = 9999

    pc = RTCPeerConnection()
    player = MediaPlayer("video.webm")
    pc.addTrack(player.video)
    video_done_future = asyncio.Future()

    offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    local_port = random.randint(50000, 60000)
    offer_message = {"type": "offer", "sdp": pc.localDescription.sdp, "client_port": local_port}

    loop = asyncio.get_event_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: ClientProtocol(offer_message, video_done_future),  # Pasar la oferta al protocolo
        remote_addr=(signalling_host, signalling_port),
        local_addr=("0.0.0.0", local_port),
    )

    protocol.connection = pc
    protocol.server_address = (signalling_host, signalling_port)

    @player.video.on("ended")
    def on_video_end():
        protocol.send_bye()

    await video_done_future
    await pc.close()


if __name__ == "__main__":
    asyncio.run(main())
