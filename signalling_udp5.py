import asyncio
import json

counter = 0

class SignallingServerProtocol(asyncio.DatagramProtocol):
    def __init__(self):
        self.clients = {}  # Diccionario {cliente: servidor asociado}
        self.servers = {}  # Diccionario {nombre_servidor: dirección_servidor}

    def connection_made(self, transport):
        self.transport = transport
        print("Servidor de señalización iniciado.")

    def datagram_received(self, data, addr):
        message = json.loads(data.decode())
        message_type = message["type"]
        global counter

        if message_type == "REGISTER":
            name_server = message["name"]
            self.servers[name_server] = addr
            print(f"Servidor '{name_server}' registrado desde {addr}")


        elif message_type == "offer":
            requested_server = message["server"]
            print(f"Cliente {addr} solicita comunicación con el servidor '{requested_server}'.")
            # Filtrar servidores registrados con el nombre solicitado
            matching_servers = [
                (server_name, server_addr) for server_name, server_addr in self.servers.items() if
                server_name == requested_server
            ]

            if matching_servers:
                # Seleccionar un servidor de la lista con índice cíclico
                selected_server = matching_servers[counter % len(matching_servers)]
                counter += 1  # Incrementar para balancear la carga
                self.clients[addr] = selected_server[1]  # Asociar cliente con servidor
                self.transport.sendto(data, selected_server[1])
                print(f"Reenviado mensaje 'offer' del cliente {addr} al servidor {selected_server[1]}")
            else:
                print(f"No se encontró un servidor registrado con el nombre '{requested_server}'.")



        elif message_type == "answer":
            # Obtener todos los clientes asociados al servidor
            matching_clients = [client for client, server in self.clients.items() if server == addr]
            if matching_clients:
                # Seleccionar el cliente correcto con índice cíclico
                client_address = matching_clients[counter % len(matching_clients)]
                counter += 1  # Incrementar para la próxima solicitud
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


if __name__ == "__main__":
    asyncio.run(main())
