#########################################
# server.py                             #
# The chat server                       #
# by Kenji Takahashi-Rial               #
#########################################

import select
import socket
import sys

from server_messaging import *


# INITIAL SETUP #################################################


IP_ADDRESS = socket.gethostname()
PORT = 1081

# Set up the server socket and start listening
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Allows reuse of address/port
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

server_socket.bind((IP_ADDRESS, PORT))
server_socket.listen()

print(f"\nListening for connections on {IP_ADDRESS}:{PORT}...\n")

# Keep track of sockets and client information
sockets = [server_socket]
clients = {}
usernames = {}

# Rooms dictionary has the room name and the list of clients currently
# inside the room
rooms = {"chat": [], "hottub": [], "PAD": [], "anime": []}


# FUNCTIONS ######################################################


def initialize_user(client_socket, client_address):
    """
    Description:
        Gets the client data and stores it in the server
    Agruments:
        A client socket to initialize
        The client's address
    Return Value:
        The client's chosen username
        False if connection was terminated or an error occurred
    """

    send_message("Welcome to the GungHo test chat server", client_socket)

    str_address = f"{client_address[0]}:{client_address[1]}"

    # Get the desired username
    while True:
        send_message("Username?: ", client_socket)
        username = get_message(client_socket)

        # Connection terminated before name given
        if not username:
            return False

        # If username is taken, continue asking
        if username in usernames:
            send_message(f"Sorry, {username} is taken", client_socket)
            continue

        break

    # Add user data to the server
    sockets.append(client_socket)
    usernames[username] = client_socket
    clients[client_socket] = (str_address, username)

    send_message(f"Welcome, {username}!", client_socket)

    return username


def connection_terminated(client_socket):
    """
    Description:
        Prints a message that a client terminated their connection and
        removes the client from the server
    Arguments:
        A client socket whos connection was or is to be terminated
    Return Value:
        None
    """

    if client_socket in clients:
        ex_client = clients[client_socket]

        print(f"\nConnection {ex_client[0]} " +
              f"terminated by client {ex_client[1]}\n")

        sockets.remove(ready_socket)
        del usernames[ex_client[1]]
        del ex_client

    else:
        print(f"\nConnection {str_address} terminated by unnamed client\n")

    # client_socket.close()


# MAIN SERVER LOOP ##################################################


while True:
    # Get the ready sockets
    read_sockets, write_sockets, error_sockets = (
        select.select(sockets, [], sockets))

    for ready_socket in read_sockets:
        # New connection
        if ready_socket == server_socket:
            client_socket, client_address = server_socket.accept()

            new_user = initialize_user(client_socket, client_address)

            if new_user:
                print(f"\nNew connection: {client_address[0]}:" +
                      f"{client_address[1]}, Username: {new_user}\n")

        # Get a message and distribute to clients
        else:
            message = get_message(ready_socket)

            # Normal message
            if message is not False:
                username = clients[ready_socket][1]

                for client_socket in clients:
                    send_message(f"{username}: {message}", client_socket)

    # Error handling
    for ready_socket in error_sockets:
        connection_terminated(ready_socket)
