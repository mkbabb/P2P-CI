import socket as sock
from pathlib import Path
from typing import *

from src.peer.server import (
    create_response_message,
    create_response_message_header,
    get_os,
    get_rfc_path,
)
from src.utils import (
    PORT,
    create_status_header,
    print_message,
    recv_message,
    send_message,
)


def add_rfc(rfc_number: int, title: str, hostname: str, port: int) -> str:
    data = dict(
        method="ADD",
        rfc_number=rfc_number,
        host=hostname,
        port=port,
        title=title,
    )
    header = create_response_message_header(data)
    return create_response_message(header, data)


def lookup_rfc(rfc_number: int, title: str, hostname: str, port: int) -> str:
    data = dict(
        method="LOOKUP",
        rfc_number=rfc_number,
        host=hostname,
        port=port,
        title=title,
    )
    header = create_response_message_header(data)
    return create_response_message(header, data)


def list_rfcs(hostname: str, port: int) -> str:
    data = dict(
        method="LISTALL",
        host=hostname,
        port=port,
    )
    header = create_response_message_header(data)
    return create_response_message(header, data)


def get_rfc(
    hostname: str,
    port: int,
    rfc_number: int,
) -> None:

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
        response = recv_message(peer_socket).decode()
        print_message(response, "Response")

        arr = response.split(" ")
        status = int(arr[1])

        if status == 200:
            print("Downloading file...")
            filepath = get_rfc_path(rfc_number)
            out_filepath = Path(filepath.name)

            with out_filepath.open("w") as file:
                while (d := recv_message(peer_socket)) :
                    file.write(d.decode())
        else:
            print("File not found!")


def peer_client(hostname: str, port: int) -> None:
    def handle(option: int) -> Optional[str]:
        if option == 1:
            rfc_number = int(input("Enter RFC number: "))
            title = input("Enter RFC title: ")

            return add_rfc(rfc_number, title, hostname, port)
        elif option == 2:
            rfc_number = int(input("Enter RFC number: "))
            title = input("Enter RFC title: ")

            return lookup_rfc(rfc_number, title, hostname, port)
        elif option == 3:
            return list_rfcs(hostname, port)
        elif option == 4:
            peer_hostname = input("Enter peer hostname: ")
            peer_port = int(input("Enter peer port: "))
            rfc_number = int(input("Enter RFC number: "))

            return get_rfc(peer_hostname, peer_port, rfc_number)  # type: ignore

        return create_status_header(400)

    address = (hostname, PORT)
    with sock.create_connection(address) as server_socket:
        print(f"Connected to server: {address}")

        while True:
            print(
                """
Select an option.
    P2S:
    1. Add RFC
    2. Lookup RFC
    3. List RFC

    P2P:
    4. Download RFC
"""
            )
            if (option := input()) == "":
                break
            else:
                if (request := handle(int(option))) is not None:
                    send_message(request.encode(), server_socket)
                    response = recv_message(server_socket).decode()
                    print_message(response, "Response")
