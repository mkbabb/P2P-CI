import platform
import socket as sock
from pathlib import Path
from typing import *

DATA_PATH = Path("data/")
PORT = 7734

DEFAULT_VERSION = "P2P-CI/1.0"


STATUS_PHRASES = {
    200: "OK",
    400: "BAD REQUEST",
    404: "NOT FOUND",
    505: "P2P-CI VERSION NOT SUPPORTED",
}


HEADER_SIZE = 10


def get_os() -> str:
    return f"{platform.system()} {platform.release()}"


def get_rfc_path(rfc_number: int) -> Path:
    return DATA_PATH.joinpath(Path(f"rfc{rfc_number}.txt"))


def create_status_header(
    status_code: int, phrase: Optional[str] = None, version: str = DEFAULT_VERSION
) -> str:
    phrase = STATUS_PHRASES.get(status_code, phrase)
    return f"{version} {status_code} {phrase}"


def parse_message(message: bytes, header_size: int = HEADER_SIZE) -> Tuple[int, bytes]:
    if len(message) == 0:
        return 0, message
    else:
        message_length = int(message[:header_size].decode())
        data = message[header_size:]
        return message_length, data


def recv_message(
    peer_socket: sock.socket, header_size: int = HEADER_SIZE, chunk_size: int = 1024
) -> bytes:
    message = b""
    message_len, _ = parse_message(peer_socket.recv(header_size), header_size)

    while message_len > 0:
        chunk_size = min(chunk_size, message_len)
        message_len -= chunk_size

        response = peer_socket.recv(chunk_size)
        message += response

    return message


def send_message(
    data: bytes, peer_socket: sock.socket, header_size: int = HEADER_SIZE
) -> int:
    header = f"{len(data):<{header_size}}"
    message = header.encode() + data
    return peer_socket.send(message)


def print_message(message: str, kind: str = "Request") -> None:
    print("")
    print(f"****** {kind} ******")
    print(message)
    print("*********************")
    print("")
