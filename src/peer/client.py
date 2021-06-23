import socket as sock
from typing import *

from src.peer.server import (
    create_response_message,
    create_response_message_header,
    get_os,
    get_RFC_path,
)
from src.server import PORT, create_status_header


def add_RFC() -> str:
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


def lookup_RFC() -> str:
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


def list_RFCs() -> str:
    data = dict(
        method="LISTALL",
        host=sock.gethostname(),
        port=PORT,
    )
    header = create_response_message_header(data)
    return create_response_message(header, data)


def get_RFC() -> str:
    hostname = input("Enter hostname: ")
    port = int(input("Enter port: "))
    rfc_number = int(input("Enter RFC number: "))

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

        peer_socket.send(message.encode())

        filepath = get_RFC_path(rfc_number)

        with filepath.open("r") as file:
            while (d := peer_socket.recv(1024)) :
                file.write(d.decode())

    return create_status_header(200)


def peer_client() -> None:
    hostname = input("Enter the server hostname: ")

    with sock.create_connection((hostname, PORT)) as server_socket:

        def handle(option: int) -> str:
            if option == 1:
                return add_RFC()
            elif option == 2:
                return lookup_RFC()
            elif option == 3:
                return list_RFCs()
            elif option == 4:
                return get_RFC()
            return create_status_header(404)

        while True:
            print(
                """Select an option:
1. Add RFC
2. Lookup RFC
3. List RFC
4. Download RFC
-1. Exit"""
            )

            option = int(input())

            if option == -1:
                break

            message = handle(option)
            server_socket.send(message.encode())


if __name__ == "__main__":
    peer_client()