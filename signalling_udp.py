
# Servidor de señalización
import asyncio
import json

class SignallingServer(asyncio.DatagramProtocol):
    def __init__(self):
        self.server_address = None  # Dirección del servidor de video
        self.client_address = None  # Dirección del cliente conectado

    def connection_made(self, transport):
        self.transport = transport
        print("Servidor de señalización iniciado.")

    def datagram_received(self, data, addr):
        message = json.loads(data.decode())
        message_type = message.get("type")

        if message_type == "REGISTER":
            self.server_address = addr
            print(f"Servidor de video registrado desde {addr}")

        elif message_type == "offer":
            if self.server_address:
                self.client_address = addr
                self.transport.sendto(data, self.server_address)
                print("Oferta reenviada al servidor de video.")

        elif message_type == "answer":
            if self.client_address:
                self.transport.sendto(data, self.client_address)
                print("Respuesta reenviada al cliente.")

    def error_received(self, exc):
        print(f"Error recibido: {exc}")

async def main():
    host = "0.0.0.0"
    port = 9999

    loop = asyncio.get_event_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: SignallingServer(),
        local_addr=(host, port),
    )

    # Mantener el servidor activo
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("Servidor detenido manualmente.")

if __name__ == "__main__":
    asyncio.run(main())
