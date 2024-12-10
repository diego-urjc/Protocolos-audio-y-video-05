import asyncio
import json

class SignallingServer:
    def __init__(self, host="0.0.0.0", port=9999):
        self.host = host
        self.port = port
        self.server_address = None  # Dirección del servidor de video registrado
        self.client_to_server = {}  # Mapear clientes a servidores de video
        self.server_to_client = {}  # Mapear servidores a clientes

    async def start_server(self):
        print(f"Iniciando servidor de señalización en {self.host}:{self.port}...")
        self.transport, self.protocol = await asyncio.get_event_loop().create_datagram_endpoint(
            lambda: self,
            local_addr=(self.host, self.port),
        )
        print("Servidor listo para recibir mensajes.")

    def datagram_received(self, data, addr):
        asyncio.create_task(self.handle_message(data, addr))

    def connection_made(self, transport):
        """Se llama cuando se establece la conexión."""
        self.transport = transport

    async def handle_message(self, data, addr):
        try:
            message = json.loads(data.decode())
            message_type = message.get("type")

            if message_type == "REGISTER":
                self.server_address = addr
                print(f"Servidor de video registrado desde {addr}")

            elif message_type == "offer":
                if self.server_address:
                    self.client_to_server[addr] = self.server_address
                    self.server_to_client[self.server_address] = addr
                    self.transport.sendto(data, self.server_address)
                    print(f"Oferta reenviada de {addr} al servidor {self.server_address}")

            elif message_type == "answer":
                client_address = self.server_to_client.get(addr)
                if client_address:
                    self.transport.sendto(data, client_address)
                    print(f"Respuesta reenviada del servidor {addr} al cliente {client_address}")

            elif message_type == "bye":
                server_address = self.client_to_server.pop(addr, None)
                if server_address:
                    self.transport.sendto(data, server_address)
                    print(f"Mensaje 'bye' reenviado de {addr} al servidor {server_address}")

        except json.JSONDecodeError:
            print(f"Error al decodificar mensaje desde {addr}: {data.decode()}")

    def error_received(self, exc):
        print(f"Error recibido: {exc}")

    def connection_lost(self, exc):
        print("Conexión perdida con el servidor de señalización.")


async def main():
    server = SignallingServer()
    await server.start_server()

    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("\nServidor detenido manualmente.")


if __name__ == "__main__":
    asyncio.run(main())
