import socket as sock
import sys
import threading
from dataclasses import dataclass
from typing import *

from src.utils import (
    create_status_header,
    print_message,
    recv_message,
    send_message,
    PORT,
)


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
        return create_status_header(404)


def delete_peer(response: str) -> str:
    arr = response.split("\n")
    hostname = parse_field(arr[1])
    port = int(parse_field(arr[2]))

    peer = Peer(hostname, port)

    try:
        ACTIVE_PEERS.pop(peer)
        rfcs = [rfc for rfc in ACTIVE_RFCS if rfc.peer == peer]
        for rfc in rfcs:
            ACTIVE_RFCS.pop(rfc)

        header = create_status_header(200)
        return f"{header}\n" + f"{peer}\n" + "\n".join(map(str, rfcs))
    except KeyError:
        return create_status_header(404)


def server_receiver(peer_socket: sock.socket) -> None:
    def handle(response: str, request_type: str) -> str:
        if request_type == "ADD":
            return add_rfc(response)
        elif request_type == "LOOKUP":
            return lookup_rfc(response)
        elif request_type == "LISTALL":
            return list_rfcs()
        elif request_type == "DEL":
            return delete_peer(response)
        else:
            return create_status_header(400)

    try:
        while (request := recv_message(peer_socket).decode()) :
            print_message(request)

            arr = request.split(" ")
            request_type = arr[0]

            message = handle(request, request_type)
            send_message(message.encode(), peer_socket)
    except KeyboardInterrupt:
        pass

    peer_socket.close()
    sys.exit(0)


def server() -> None:
    address = (sock.gethostname(), PORT)

    server_socket = sock.socket(sock.AF_INET, sock.SOCK_STREAM)
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
    server()
