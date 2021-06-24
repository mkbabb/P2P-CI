# P2P-CI

Simple implementation of a peer-to-peer (P2P) and peer-to-server (P2S) system, utilizing
a centralized index (CI). In this case, the centralized index supports simple add,
lookup, and delete operations on [`RFC`](https://www.rfc-editor.org/retrieve/bulk/)
objects, whereof are defined by a `RFC number` and `RFC title`.

A main server, housing the centralized index, is defined within
[`server/server.py`](src/server/server.py). Each peer is composed of two components, a
client, [`peer/client.py`](src/peer/client.py), and a server,
[`peer/server.py`](src/peer/server.py).

**This project requires `Python 3.9>=`.**

Completed as a final project for **CSC 401** at **NCSU**. See the
[project outline](docs/proj1.pdf) for more information.

## Quickstart

To run, follow these steps:

**From the base project directory:**

1. Run the main server: `python3 -m src.server.server`
2. Run the peer client/server: `python3 -m src.peer.peer`

Done.

## P2S

The peer client communicates with the main server uses a request-response protocol. The
following requests are defined:

-   `ADD`: add an RFC to the centralized index.
-   `LOOKUP`: lookup an RFC in the centralized index.
-   `LISTALL`: list all RFCs in the centralized index.
-   `DEL`: delete a peer, and all corresponding RFCs, from the centralized index.

Requests from the client are output within the server's process; responses from the
sever are output within the client's process.

## P2P

Additionally, peers can communicate with each other using a similar scheme. The
following requests are defined:

-   `GET`: get an RFC from the opposing peer, downloading the result.

## `utils`

Within [`src/utils.py`](src/utils.py), a set of thin wrapper functions - on top of the
standard Python `socket` module - are defined.

Of note are the `send_message` and `recv_message` functions, which are used for all
message transactions herein. Essentially, when a message is passed through the above
functions, the processed output message contains a new byte-level header field. This
header scheme is fixed in width (configurable, but defaults to `10` bytes) and contains
only one piece of data: the message size (in bytes). Therefore, before a raw message is
sent, the header is dynamically added and set, and after a header-message is received,
the header is parsed and the data returned.
