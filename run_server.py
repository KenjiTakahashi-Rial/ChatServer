#########################################
# run_server.py                         #
# The code to run the chat server       #
# by Kenji Takahashi-Rial               #
#########################################

import os
import select
import socket

from room import Room
from server import Server


###############################################################################
#                                Initial Setup                                #
###############################################################################


IP_ADDRESS = socket.gethostbyname(socket.gethostname())
PORT = int(os.environ.get("PORT", 1081))

# Set up the server socket and start listening
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Allows reuse of address/port
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP_ADDRESS, PORT))
server_socket.listen()

print(f"\nListening for connections on {IP_ADDRESS}:{PORT}...\n")

rooms = {"chat": Room("chat", None),
         "hottub": Room("hottub", None),
         "PAD": Room("PAD", None),
         "anime": Room("anime", None)}

# Create the server object
chat_server = Server(server_socket, rooms)


###############################################################################
#                                  Main Loop                                  #
###############################################################################


while True:
    # Get the ready sockets
    read_sockets, write_sockets, error_sockets = (
        select.select(chat_server.sockets, [], chat_server.sockets))

    for ready_socket in read_sockets:
        # New connection
        if ready_socket == chat_server.socket:
            client_socket, client_address = chat_server.socket.accept()

            client_socket.send(f"<= Welcome to the GungHo chat server\r\n"
                               .encode('utf-8'))

            chat_server.initialize_client(client_socket)

        else:
            # Get client object
            client = chat_server.clients[ready_socket]

            # Get data and process it
            data = chat_server.receive(client)

            if data is not None and data is not False:
                chat_server.process(data, client)

    # Error handling
    for ready_socket in error_sockets:
        chat_server.connection_terminated(chat_server.clients[ready_socket])
