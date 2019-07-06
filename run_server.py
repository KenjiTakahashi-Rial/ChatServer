#########################################
# run_server.py                         #
# The code to run the chat server       #
# by Kenji Takahashi-Rial               #
#########################################

import os
import select
import socket

import server


# INITIAL SETUP #################################################


IP_ADDRESS = socket.gethostbyname(socket.gethostname())
PORT = int(os.environ.get("PORT", 1081))

HEADER_LENGTH = 8

# Set up the server socket and start listening
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Allows reuse of address/port
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP_ADDRESS, PORT))
server_socket.listen()

print(f"\nListening for connections on {IP_ADDRESS}:{PORT}...\n")

rooms = {"chat": [], "hottub": [], "PAD": [], "anime": []}

# Create the server object
chat_server = server.Server(server_socket, rooms, HEADER_LENGTH)


# MAIN SERVER LOOP ##################################################


while True:
    # Get the ready sockets
    read_sockets, write_sockets, error_sockets = (
        select.select(chat_server.sockets, [], chat_server.sockets))

    for ready_socket in read_sockets:
        # New connection
        if ready_socket == chat_server.socket:
            client_socket, client_address = chat_server.socket.accept()

            new_user = chat_server.initialize_user(client_socket)

            if new_user is not False:
                print(f"\nNew connection: {new_user.address}, " +
                      f"Username: {new_user.username}\n")

        # Get data and process it
        else:
            data = chat_server.receive(ready_socket)

            if type(data) is not bool:
                chat_server.process(data, ready_socket)

    # Error handling
    for ready_socket in error_sockets:
        chat_server.connection_terminated(ready_socket)
