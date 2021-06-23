from .client import peer_client
from .server import peer_server

import threading


def main() -> None:
    port = int(input("Enter port: "))

    peer_client_thread = threading.Thread(target=peer_client)
    peer_client_thread.setDaemon(True)
    peer_client_thread.start()

    connect_server_thread = threading.Thread(
        target=peer_server,
        args=(
            "peer-server-local",
            port,
        ),
    )
    connect_server_thread.setDaemon(True)
    connect_server_thread.start()

    connect_server_thread.join()
    peer_client_thread.join()


if __name__ == "__main__":
    main()