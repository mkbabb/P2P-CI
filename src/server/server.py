import socket as sock
import sys
import threading
from dataclasses import dataclass
from socket import socket
from typing import *
from pathlib import Path


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


def create_status_header(
    status_code: int, phrase: Optional[str] = None, version: str = DEFAULT_VERSION
) -> str:
    phrase = STATUS_PHRASES.get(status_code, phrase)
    return f"{version} {status_code} {phrase}"


def create_message(data: bytes, header_size: int = HEADER_SIZE) -> bytes:
    header = f"{len(data):<{header_size}}"
    return header.encode() + data


def parse_message(message: bytes, header_size: int = HEADER_SIZE) -> Tuple[int, bytes]:
    if len(message) == 0:
        return 0, message
    else:
        message_length = int(message[:header_size].decode())
        data = message[header_size:]
        return message_length, data


def recv_message(
    peer_socket: socket, header_size: int = HEADER_SIZE, chunk_size: int = 1024
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
    data: bytes, peer_socket: socket, header_size: int = HEADER_SIZE
) -> int:
    message = create_message(data, header_size)
    return peer_socket.send(message)


@dataclass(frozen=True)
class Peer:
    hostname: str
    port: int

    def __repr__(self) -> str:
        return f"{self.hostname} {self.port}"


@dataclass(frozen=True)
class RFC:
    rfc_number: int
    title: str
    peer: Peer

    def __repr__(self) -> str:
        return f"RFC {self.rfc_number} {self.title} {self.peer}"


ACTIVE_PEERS: Dict[Peer, Peer] = {}
ACTIVE_RFCS: Dict[RFC, RFC] = {}


def parse_field(field: str) -> str:
    return field.split(":", 1)[1]


def parse_request_message(response: str) -> dict:
    arr = response.split("\n")

    method, _, rfc_number, version = arr[0].split(" ")
    hostname = parse_field(arr[1])
    port = int(parse_field(arr[2]))
    title = parse_field(arr[3])

    return dict(
        method=method,
        hostname=hostname,
        port=port,
        version=version,
        rfc_number=rfc_number,
        title=title,
    )


def get_peer(hostname: str, port: int) -> Peer:
    peer = Peer(hostname, port)
    return ACTIVE_PEERS.setdefault(peer, peer)


def get_rfc(rfc_number: int, title: str, peer: Peer) -> RFC:
    rfc = RFC(rfc_number, title, peer)
    return ACTIVE_RFCS.setdefault(rfc, rfc)


def get_rfcs(rfc_number: int, title: str) -> List[RFC]:
    return [
        rfc
        for rfc in ACTIVE_RFCS
        if rfc.rfc_number == rfc_number and rfc.title == title
    ]


def add_rfc(response: str) -> str:
    request_message = parse_request_message(response)
    peer = get_peer(request_message["hostname"], request_message["port"])
    rfc = get_rfc(request_message["rfc_number"], request_message["title"], peer)

    header = create_status_header(200)

    return f"{header}\n{rfc}"


def lookup_rfc(response: str) -> str:
    request_message = parse_request_message(response)
    rfcs = get_rfcs(request_message["rfc_number"], request_message["title"])

    if len(rfcs) > 0:
        header = create_status_header(200)
        return f"{header}\n" + "\n".join(map(str, rfcs))
    else:
        return create_status_header(404)


def list_rfcs() -> str:
    if len(ACTIVE_RFCS) > 0:
        header = create_status_header(200)
        return f"{header}\n" + "\n".join(map(str, ACTIVE_RFCS))
    else:
        return create_status_header(400)


def server_receiver(peer_socket: socket) -> None:
    def handle(response: str, request_type: str) -> str:
        if request_type == "ADD":
            return add_rfc(response)
        elif request_type == "LOOKUP":
            return lookup_rfc(response)
        elif request_type == "LISTALL":
            return list_rfcs()
        return create_status_header(400)

    try:
        while True:
            request = recv_message(peer_socket).decode()
            print(request, "\n")

            arr = request.split(" ")
            request_type = arr[0]

            message = handle(request, request_type)
            send_message(message.encode(), peer_socket)

    except KeyboardInterrupt:
        peer_socket.close()
        sys.exit(0)


def main() -> None:
    address = (sock.gethostname(), PORT)

    server_socket = socket(sock.AF_INET, sock.SOCK_STREAM)
    server_socket.bind(address)
    server_socket.listen(32)

    print(f"Started server: {address}")

    try:
        while True:
            conn, _ = server_socket.accept()
            t = threading.Thread(target=server_receiver, args=(conn,))
            t.start()
    except KeyboardInterrupt:
        server_socket.close()
        sys.exit(0)


if __name__ == "__main__":
    main()