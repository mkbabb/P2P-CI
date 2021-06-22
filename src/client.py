import socket as sock
import sys
import threading
from dataclasses import dataclass
from socket import socket
from typing import *

from server import HOSTNAME, PORT, RFC, Peer
