import socket as sock
from pathlib import Path
from src import server
from src.server.server import recv_message, send_message
from typing import *

from src.peer.server import (
    create_response_message,
    create_response_message_header,
    get_os,
    get_rfc_path,
)
from src.server import PORT, create_status_header


def add_rfc() -> str:
    rfc_number = int(input("Enter RFC number: "))
    title = input("Enter RFC title: ")

    data = dict(
        method="ADD",
        rfc_number=rfc_number,
        host=sock.gethostname(),
        port=PORT,
        title=title,
    )
    header = create_response_message_header(data)
    return create_response_message(header, data)


def lookup_rfc() -> str:
    rfc_number = input("Enter RFC number: ")
    title = input("Enter RFC title: ")

    data = dict(
        method="LOOKUP",
        rfc_number=rfc_number,
        host=sock.gethostname(),
        port=PORT,
        title=title,
    )
    header = create_response_message_header(data)
    return create_response_message(header, data)


def list_rfcs() -> str:
    data = dict(
        method="LISTALL",
        host=sock.gethostname(),
        port=PORT,
    )
    header = create_response_message_header(data)
    return create_response_message(header, data)


def get_rfc() -> None:
    # hostname = input("Enter peer hostname: ")
    # port = int(input("Enter peer port: "))
    # rfc_number = int(input("Enter RFC number: "))

    hostname = sock.gethostname()
    port = 1234
    rfc_number = 1

    with sock.create_connection((hostname, port)) as peer_socket:
        data = dict(
            method="GET",
            rfc_number=rfc_number,
            host=hostname,
            port=port,
            os=get_os(),
        )
        header = create_response_message_header(data)
        message = create_response_message(header, data)

        send_message(message.encode(), peer_socket)
        response = recv_message(peer_socket)

        print(response.decode(), "\n")

        filepath = get_rfc_path(rfc_number)
        out_filepath = Path(filepath.name)

        with out_filepath.open("w") as file:
            while (d := recv_message(peer_socket)) :
                file.write(d.decode())


def peer_client() -> None:
    def handle(option: int) -> Optional[str]:
        if option == 1:
            return add_rfc()
        elif option == 2:
            return lookup_rfc()
        elif option == 3:
            return list_rfcs()
        elif option == 4:
            return get_rfc()  # type: ignore
        return create_status_header(400)

    # hostname = input("Enter the server hostname: ")
    hostname = sock.gethostname()
    address = (hostname, PORT)

    print(f"Started server: {address}")

    with sock.create_connection(address) as server_socket:
        while True:
            print(
                """
Select an option:
1. Add RFC
2. Lookup RFC
3. List RFC
4. Download RFC
"""
            )
            if (option := input()) == "":
                break
            else:
                if (request := handle(int(option))) is not None:
                    send_message(request.encode(), server_socket)
                    response = recv_message(server_socket)
                    print(response.decode(), "\n")


if __name__ == "__main__":
    peer_client()
