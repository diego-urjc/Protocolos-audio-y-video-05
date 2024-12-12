import asyncio
import json

counter = 0

class SignallingServerProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.clients = {}  # Diccionario de clientes y servidores asociados {cliente: servidor}
        self.servers = set()  # Lista de servidores de video registrados

    def connection_made(self, transport):
        self.transport = transport
        print("Servidor de señalización iniciado.")

    def datagram_received(self, data, addr):
        global counter

        message = json.loads(data.decode())
        message_type = message["type"]

        if message_type == "REGISTER":
            self.servers.add(addr)
            print(f"Servidor de video registrado desde {addr}")

        elif message_type == "offer":
            server_address = next(iter(self.servers), None)
            if server_address:
                self.clients[addr] = server_address
                self.transport.sendto(data, server_address)
                print(f"Reenviado mensaje 'offer' del cliente {addr} al servidor {server_address}")
            else:
                print("No hay servidores de video registrados.")


        elif message_type == "answer":
            # Obtener todos los clientes asociados al servidor
            matching_clients = [client for client, server in self.clients.items() if server == addr]

            if matching_clients:
                # Seleccionar el cliente correcto (podemos usar un criterio adicional si es necesario)
                client_address = matching_clients[counter]
                counter += 1  # Por ahora seleccionamos el primero
                self.transport.sendto(data, client_address)
                print(f"Reenviado mensaje 'answer' del servidor {addr} al cliente {client_address}")
            else:
                print(f"No se encontró cliente asociado a la dirección {addr}.")


        elif message_type == "bye":
            self.clients.pop(addr, None)
            print(f"Mensaje 'bye' procesado para cliente {addr}.")


async def main():
    signalling_host = "0.0.0.0"
    signalling_port = 9999

    loop = asyncio.get_event_loop()
    transport, protocol = await loop.create_datagram_endpoint(
        lambda: SignallingServerProtocol(),
        local_addr=(signalling_host, signalling_port),
    )

    print(f"Iniciando servidor de señalización en {signalling_host}:{signalling_port}...")
    try:
        while True:
            await asyncio.sleep(3600)
    except KeyboardInterrupt:
        print("Servidor detenido manualmente.")
#comentario para hacer commit


if __name__ == "__main__":
    asyncio.run(main())
