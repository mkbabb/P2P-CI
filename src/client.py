import socket as sock
import sys
import threading
from dataclasses import dataclass
from socket import socket
from typing import *

from server import DEFAULT_VERSION, HOSTNAME, PORT, RFC, Peer, create_message_header


def create_response_message(response: dict) -> str:
    header_arr = [response.pop("method")]
    
    if "rfc_number" in response:
        rfc_number = response.pop("rfc_number")
        header_arr.append(f"RFC {rfc_number}")

    header_arr.append(DEFAULT_VERSION)

    arr = [" ".join(header_arr)]
    arr.extend([f"{str(k).capitalize()}: {v}" for k, v in response.items()])

    return "\n".join(arr)


def add_RFC() -> dict:
    rfc_number = input("Enter RFC number: ")
    title = input("Enter RFC title: ")

    return dict(
        method="ADD",
        rfc_number=int(rfc_number),
        hostname=HOSTNAME,
        port=PORT,
        title=title,
    )


def lookup_RFC() -> dict:
    rfc_number = input("Enter RFC number: ")
    title = input("Enter RFC title: ")

    return dict(
        method="LOOKUP",
        rfc_number=int(rfc_number),
        hostname=HOSTNAME,
        port=PORT,
        title=title,
    )


def list_rfcs() -> dict:
    return dict(
        method="LISTALL",
        hostname=HOSTNAME,
        port=PORT,
    )
