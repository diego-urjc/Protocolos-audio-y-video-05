import asyncio
import json

class SignallingServer:
    def __init__(self, host="0.0.0.0", port=9999):
        self.host = host
        self.port = port
        self.server_address = None  # Dirección del servidor de video registrado
        self.clients = {}  # Dirección de los clientes que envían ofertas

    async def start_server(self):
        print(f"Iniciando servidor de señalización en {self.host}:{self.port}...")
        # Crear transporte y protocolo UDP
        self.transport, self.protocol = await asyncio.get_event_loop().create_datagram_endpoint(
            lambda: self,
            local_addr=(self.host, self.port),
        )


    def connection_made(self, transport):
        """Se llama cuando se establece la conexión."""
        self.transport = transport

    def datagram_received(self, data, addr):
        """Se llama al recibir un datagrama."""
        try:
            message = json.loads(data.decode())
            message_type = message.get("type")

            if message_type == "REGISTER":
                self.server_address = addr
                print(f"Servidor de video registrado desde {addr}")

            elif message["type"] == "bye":
                print("Mensaje bye recibido desde el cliente. Reenviando mensaje de despedida al servidor de video...")
                self.transport.sendto(data, self.server_address)



            elif message_type == "offer":
                if self.server_address:
                    self.clients[addr] = self.server_address
                    self.transport.sendto(data, self.server_address)
                    print(f"Reenviado mensaje 'offer' del cliente {addr} al servidor {self.server_address}")
                else:
                    print("No hay servidor registrado para enviar la oferta.")

            elif message_type == "answer":
                client_address = next(
                    (client for client, server in self.clients.items() if server == addr),
                    None
                )
                if client_address:
                    self.transport.sendto(data, client_address)
                    print(f"Reenviado mensaje 'answer' del servidor {addr} al cliente {client_address}")
                else:
                    print("No se encontró cliente para enviar la respuesta.")

        except json.JSONDecodeError:
            print(f"Error al decodificar mensaje desde {addr}: {data.decode()}")

    def error_received(self, exc):
        """Se llama si ocurre un error."""
        print(f"Error recibido: {exc}")

    def connection_lost(self, exc):
        """Se llama cuando se pierde la conexión."""
        print("Conexión perdida con el servidor de señalización.")

async def main():
    server = SignallingServer()
    await server.start_server()

    # Mantener el servidor activo
    try:
        while True:
            await asyncio.sleep(3600)  # Mantener el servidor en ejecución
    except KeyboardInterrupt:
        print("\nServidor detenido manualmente.")

if __name__ == "__main__":
    asyncio.run(main())
