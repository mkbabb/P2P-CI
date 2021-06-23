import os
import platform
import socket as sock
from src.server.server import PORT
import sys
import threading
import time
from pathlib import Path
from socket import socket
from typing import *

from src.server import DATA_PATH, DEFAULT_VERSION, create_status_header


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


def get_os() -> str:
    return f"{platform.system()} {platform.release()}"


def get_rfc_path(rfc_number: int) -> Path:
    return DATA_PATH.joinpath(Path(f"rfc{rfc_number}.txt"))


def get_rfc(peer_socket: socket, response: str) -> str:
    TIME_FMT = "%a, %d %b %Y %H:%M:%S"

    arr = response.split(" ")
    filepath = get_rfc_path(int(arr[2]))

    if filepath.is_file():
        last_modified = (
            time.strftime(TIME_FMT, time.gmtime(os.path.getmtime(filepath))) + " GMT\n"
        )
        OS = get_os()
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
            return get_rfc(peer_socket, response)
        return create_status_header(400)

    try:
        response = peer_socket.recv(1024).decode()
        print(response, "\n")

        arr = response.split(" ")
        request_type = arr[0]
        message = handle(response, request_type)
        print(message, "\n")

        peer_socket.close()
    except KeyboardInterrupt:
        peer_socket.close()
        sys.exit(0)


def peer_server(hostname: str, port: int) -> None:
    peer_socket = socket(sock.AF_INET, sock.SOCK_STREAM)
    peer_socket.bind((hostname, port))
    peer_socket.listen(32)

    try:
        while True:
            conn, _ = peer_socket.accept()
            t = threading.Thread(target=peer_receiver, args=(conn,))
            t.start()
    except KeyboardInterrupt:
        peer_socket.close()
        sys.exit(0)


if __name__ == "__main__":
    # hostname = input("Enter hostname: ")
    # port = int(input("Enter port: "))
    hostname = sock.gethostname()
    port = 1234

    address = (hostname, port)
    print(f"Started server: {address}")

    peer_server(hostname, port)