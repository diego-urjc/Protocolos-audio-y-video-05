# Servidor de video
import asyncio
import json
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder

class VideoServerProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.server_address = None  # Dirección del servidor de señalización
        self.pc = None  # Única instancia de RTCPeerConnection
        self.recorder = None  # Única instancia de MediaRecorder

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
            print("Oferta recibida. Procesando...")
            asyncio.create_task(self.handle_offer(message))

        elif message["type"] == "bye":
            print("Mensaje 'bye' recibido. Finalizando grabación...")
            asyncio.create_task(self.cleanup())

    async def handle_offer(self, message):
        self.pc = RTCPeerConnection()
        self.recorder = MediaRecorder("video-out.mp4")

        @self.pc.on("track")
        async def on_track(track):
            print("Recibiendo video...")
            self.recorder.addTrack(track)
            await self.recorder.start()
            print("Grabación iniciada")

            @track.on("ended")
            async def on_ended():
                print("Track terminado. Deteniendo grabación...")
                await self.cleanup()

        offer = RTCSessionDescription(message["sdp"], message["type"])
        await self.pc.setRemoteDescription(offer)
        answer = await self.pc.createAnswer()
        await self.pc.setLocalDescription(answer)

        answer_message = {"type": "answer", "sdp": self.pc.localDescription.sdp}
        self.transport.sendto(json.dumps(answer_message).encode(), self.server_address)
        print("Respuesta enviada.")

    async def cleanup(self):
        if self.recorder:
            await self.recorder.stop()
            print("Grabación finalizada y guardada como 'video-out.mp4'.")
        if self.pc:
            await self.pc.close()
            print("Conexión RTC cerrada.")
        self.pc = None
        self.recorder = None

async def main():
    signalling_host = "127.0.0.1"
    signalling_port = 9999

    loop = asyncio.get_event_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: VideoServerProtocol(),
        remote_addr=(signalling_host, signalling_port),
        local_addr=("0.0.0.0", 12345),
    )

    # Mantener el servidor activo
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("Servidor detenido manualmente.")
#comentario para hacer commit

if __name__ == "__main__":
    asyncio.run(main())

