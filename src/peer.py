import os
import platform
import socket as sock
import sys
import threading
import time
from pathlib import Path
from socket import socket
from typing import *

from server import DEFAULT_VERSION, HOSTNAME, PORT, RFC, Peer, create_status_header


def create_response_message(header: str, data: dict) -> str:
    arr = [header]
    arr.extend([f"{str(k).upper()}: {v}" for k, v in data.items()])
    return "\n".join(arr)


def create_response_message_header(data: dict) -> str:
    header_arr = [data.pop("method")]
    if "rfc_number" in data:
        rfc_number = data.pop("rfc_number")
        header_arr.append(f"RFC {rfc_number}")
    header_arr.append(DEFAULT_VERSION)
    return " ".join(header_arr)


def add_RFC() -> str:
    rfc_number = input("Enter RFC number: ")
    title = input("Enter RFC title: ")

    data = dict(
        method="ADD",
        rfc_number=int(rfc_number),
        host=HOSTNAME,
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
        rfc_number=int(rfc_number),
        host=HOSTNAME,
        port=PORT,
        title=title,
    )
    header = create_response_message_header(data)
    return create_response_message(header, data)


def list_RFCs() -> str:
    data = dict(
        method="LISTALL",
        host=HOSTNAME,
        port=PORT,
    )
    header = create_response_message_header(data)
    return create_response_message(header, data)


def get_RFC(peer_socket: socket, response: str) -> str:
    TIME_FMT = "%a, %d %b %Y %H:%M:%S"

    arr = response.split(" ")
    filepath = Path(f"RFC{arr[2]}.txt")

    if filepath.is_file():
        last_modified = (
            time.strftime(TIME_FMT, time.gmtime(os.path.getmtime(filepath))) + " GMT\n"
        )
        OS = f"{platform.system()} {platform.release()}"
        curr_time = time.strftime(TIME_FMT, time.gmtime()) + "GMT\n"
        file_size = os.path.getsize(filepath)

        header = create_status_header(200)
        data = {
            "date": curr_time,
            "os": OS,
            "last-modified": last_modified,
            "content-length": file_size,
            "content-type": "text/text",
        }
        message = create_response_message(header, data)
        peer_socket.send(message.encode())

        with filepath.open("r") as file:
            while (d := file.read(1024)) :
                peer_socket.send(d.encode())

        return create_status_header(200)


def peer_receiver(peer_socket: socket) -> None:
    def handle(response: str, request_type: str) -> str:
        if request_type == "GET":
            return get_RFC(peer_socket, response)
        return create_status_header(404)

    try:
        while True:
            response = peer_socket.recv(1024).decode()
            print(response)

            if len(response) == 0:
                peer_socket.close()
                return

            arr = response.split(" ")
            request_type = arr[0]

            message = handle(response, request_type)
            peer_socket.send(message.encode())
    except KeyboardInterrupt:
        peer_socket.close()
        sys.exit(0)


def peer_server(peer_port: int) -> None:
    peer_socket = socket(sock.AF_INET, sock.SOCK_STREAM)
    peer_socket.bind((HOSTNAME, peer_port))

    try:
        while True:
            peer_socket.listen(8)
            conn, _ = peer_socket.accept()
            t = threading.Thread(target=peer_receiver, args=(conn,))
            t.start()
    except KeyboardInterrupt:
        peer_socket.close()
        sys.exit(0)


def connect_to_server():
    servername = input("Enter the server IP: ")
    server_socket = socket(sock.AF_INET, sock.SOCK_STREAM)

    server_socket.connect((HOSTNAME, PORT))

    def handle(option: int):
        if option == 1:
            return add_RFC()
        elif option == 2:
            return lookup_RFC()
        elif option == 3:
            return list_RFCs()
        elif option == 4:
            pass

    while True:
        print(
            """Select an option:
1. Add RFC
2. Lookup RFC
3. List RFC
4. Download RFC"""
        )
        option = int(input())
        message = handle(option)
        server_socket.send(message.encode())
