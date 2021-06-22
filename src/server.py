import socket as sock
import sys
from dataclasses import dataclass
from socket import socket
from typing import *
import threading

HOSTNAME = sock.gethostname()
PORT = 7734

DEFAULT_VERSION = "P2P-CI/1.0"

STATUS_PHRASES = {
    200: "OK",
    400: "BAD REQUEST",
    404: "NOT FOUND",
    505: "P2P-CI VERSION NOT SUPPORTED",
}


def create_message_header(
    status_code: int, phrase: Optional[str] = None, version: str = DEFAULT_VERSION
) -> str:
    phrase = STATUS_PHRASES.get(status_code, phrase)
    return f"{version} {status_code} {phrase}"


@dataclass
class Peer:
    hostname: str
    port: int


@dataclass
class RFC:
    rfc_number: int
    title: str
    peer: Peer

    def __repr__(self) -> str:
        return f"RFC {self.rfc_number} {self.title} {self.peer}"


ACTIVE_PEERS: List[Peer] = []
ACTIVE_RFCS: List[RFC] = []


def parse_field(field: str) -> str:
    return field.split(":", 1)[1]


def parse_request_message(response: str) -> dict:
    arr = response.split("\n")

    method, rfc_number, version = arr[0].split(" ")
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
    ix = ACTIVE_PEERS.index(peer)

    if ix == -1:
        ACTIVE_PEERS.append(peer)
    else:
        peer = ACTIVE_PEERS[ix]

    return peer


def get_rfcs(rfc_number: int, title: str) -> List[RFC]:
    return [
        rfc
        for rfc in ACTIVE_RFCS
        if rfc.rfc_number == rfc_number and rfc.title == title
    ]


def add_RFC(response: str) -> str:
    request_message = parse_request_message(response)
    peer = get_peer(request_message["hostname"], request_message["port"])

    rfc = RFC(request_message["rfc_number"], request_message["title"], peer)
    header = create_message_header(200)

    return f"{header}\n{rfc}"


def lookup_RFC(response: str) -> str:
    request_message = parse_request_message(response)
    rfcs = get_rfcs(request_message["rfc_number"], request_message["title"])

    if len(rfcs) > 0:
        header = create_message_header(200)
        return f"{header}\n" + "\n".join(map(str, rfcs))
    else:
        return create_message_header(404)


def list_rfcs() -> str:
    if len(ACTIVE_RFCS) > 0:
        header = create_message_header(200)
        return f"{header}\n" + "\n".join(map(str, ACTIVE_RFCS))
    else:
        return create_message_header(404)


def peer_receiver(peer_socket: socket) -> None:
    def handle(response: str, request_type: str) -> str:
        if request_type == "ADD":
            return add_RFC(response)
        elif request_type == "LOOKUP":
            return lookup_RFC(response)
        elif request_type == "LIST":
            return list_rfcs()
        else:
            return create_message_header(404)

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


def main() -> None:

    server_socket = socket(sock.AF_INET, sock.SOCK_STREAM)
    server_socket.bind((HOSTNAME, PORT))

    try:
        while True:
            server_socket.listen(32)
            peer_socket, _ = server_socket.accept()
            t = threading.Thread(target=peer_receiver, args=(peer_socket,))
            t.start()
    except KeyboardInterrupt:
        server_socket.close()
        sys.exit(0)


if __name__ == "__main__":
    main()