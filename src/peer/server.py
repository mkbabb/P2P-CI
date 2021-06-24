import os
import socket as sock
import sys
import threading
import time
from socket import socket
from typing import *

from src.utils import (
    DEFAULT_VERSION,
    create_status_header,
    get_os,
    get_rfc_path,
    print_message,
    recv_message,
    send_message,
)


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


def get_rfc(peer_socket: socket, response: str) -> None:
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
        send_message(message.encode(), peer_socket)

        with filepath.open("r") as file:
            while (d := file.read(1024)) :
                send_message(d.encode(), peer_socket)
    else:
        message = create_status_header(404)
        send_message(message.encode(), peer_socket)


def peer_receiver(peer_socket: socket) -> None:
    def handle(response: str, request_type: str) -> Optional[str]:
        if request_type == "GET":
            return get_rfc(peer_socket, response)  # type: ignore
        else:
            return create_status_header(400)

    try:
        request = recv_message(peer_socket).decode()
        print_message(request)

        arr = request.split(" ")
        request_type = arr[0]
        message = handle(request, request_type)
    except KeyboardInterrupt:
        pass

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
