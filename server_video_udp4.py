import asyncio
import json
from aiortc import RTCPeerConnection, RTCSessionDescription
from aiortc.contrib.media import MediaRecorder

counter_s= 0

class VideoServerProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.server_address = None
        self.clients = {}

    def connection_made(self, transport):
        self.transport = transport
        print("Conexión con el servidor de señalización establecida.")
        register_message = {"type": "REGISTER"}
        self.transport.sendto(json.dumps(register_message).encode(), self.server_address)

    def datagram_received(self, data, addr):
        message = json.loads(data.decode())
        if message["type"] == "offer":
            asyncio.create_task(self.handle_offer(message, addr))
        elif message["type"] == "bye":
            client = self.clients.pop(addr, None)
            if client:
                print(f"Finalizando conexión para cliente {addr}.")
            else:
                print(f"Cliente {addr} no encontrado.")

    async def handle_offer(self, message, addr):
        global counter_s
        counter_s += 1
        pc = RTCPeerConnection()
        recorder = MediaRecorder(f"video-{counter_s}.mp4")

        @pc.on("track")
        async def on_track(track):
            recorder.addTrack(track)
            await recorder.start()
            print(f"Grabación iniciada para cliente {addr}")

            @track.on("ended")
            async def on_ended():
                await recorder.stop()
                print(f"Grabación finalizada para cliente {addr}.")

        offer = RTCSessionDescription(message["sdp"], message["type"])
        await pc.setRemoteDescription(offer)
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)

        self.clients[addr] = (pc, recorder)

        answer_message = {"type": "answer", "sdp": pc.localDescription.sdp}
        self.transport.sendto(json.dumps(answer_message).encode(), self.server_address)


async def main():
    signalling_host = "127.0.0.1"
    signalling_port = 9999

    loop = asyncio.get_event_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: VideoServerProtocol(),
        remote_addr=(signalling_host, signalling_port),
        local_addr=("0.0.0.0", 12345),
    )

    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("Servidor detenido manualmente.")


if __name__ == "__main__":
    asyncio.run(main())
