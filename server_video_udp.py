import asyncio
import json
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder


class VideoServerProtocol(asyncio.DatagramProtocol):
    def __init__(self, pc, recorder, on_ready):
        self.pc = pc
        self.recorder = recorder
        self.on_ready = on_ready
        self.server_address = None  # Dirección del servidor de señalización

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
            print("Oferta recibida del cliente. Procesando...")
            asyncio.create_task(self.handle_offer(message))

    async def handle_offer(self, message):
        offer = RTCSessionDescription(message["sdp"], message["type"])
        await self.pc.setRemoteDescription(offer)

        # Crear y enviar respuesta
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)
        answer_message = {"type": "answer", "sdp": self.pc.localDescription.sdp}
        self.transport.sendto(json.dumps(answer_message).encode(), self.server_address)
        print("Respuesta enviada al cliente.")

    def error_received(self, exc):
        print(f"Error recibido: {exc}")

    def connection_lost(self, exc):
        print("Conexión perdida con el servidor de señalización.")
        self.on_ready.set_result(True)


async def main():
    signalling_host = "127.0.0.1"
    signalling_port = 9999

    # Configuración de WebRTC
    pc = RTCPeerConnection()
    recorder = MediaRecorder("video-out.mp4")
    ready_future = asyncio.Future()

    @pc.on("track")
    def on_track(track):
        print("Recibiendo video...")
        recorder.addTrack(track)

    await recorder.start()

    # Crear transporte UDP con protocolo de servidor de video
    loop = asyncio.get_event_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: VideoServerProtocol(pc, recorder, ready_future),
        remote_addr=(signalling_host, signalling_port),
        local_addr=("0.0.0.0", 12345),  # Puerto fijo donde escucha este servidor
    )

    # Esperar hasta que el protocolo indique que ha terminado
    await ready_future

    await recorder.stop()
    await pc.close()


if __name__ == "__main__":
    asyncio.run(main())
