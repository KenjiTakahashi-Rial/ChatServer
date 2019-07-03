#########################################
# Chat Server                           #
# GungHo engineering test               #
# by Kenji Takahashi-Rial               #
#########################################

import socket
import select

IP_ADDRESS = socket.gethostname()
PORT = 1081

# Use a header to know how long a message will be
HEADER_LENGTH = 8

# Set up the server socket and start listening
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((IP_ADDRESS, PORT))
server_socket.listen()

# DEBUG
print(f"\nListening for connections on {IP_ADDRESS}:{PORT}...\n")

# Keep track of sockets and client information
sockets = [server_socket]
clients = {}
usernames = {}


def initialize_user(client_socket):
    """
    Description:
        Gets the client data and stores it in the server
    Agruments:
        A client socket to initialize
    Return Value:
        Returns the new client's username
    """

    user = receive_data(client_socket)

    sockets.append(client_socket)
    clients[client_socket] = user

    username = user['message'].decode('utf-8')
    usernames[username] = client_socket

    return username


def receive_data(client_socket):
    """
    Description:
        Handles receiving data from a client
    Arguments:
        A client socket to receive data from
    Return Value:
        A dictionary with the encoded header and message data
    """

    header = client_socket.recv(HEADER_LENGTH)
    msg_len = int(header.decode('utf-8').strip())
    message = client_socket.recv(msg_len)

    return {'header': header, 'message': message}


# Main server loop
while True:
    # Get the ready sockets
    read_sockets, write_sockets, error_sockets = (
        select.select(sockets, [], sockets))

    for ready_socket in read_sockets:
        # New connection
        if ready_socket == server_socket:
            client_socket, client_address = server_socket.accept()

            new_user = initialize_user(client_socket)

            print(f"\nNew connection: {client_address[0]}:{client_address[1]}",
                  f", Username: {new_user}\n")

        # Receive data and distribute message to clients
        else:
            data = receive_data(ready_socket)
            user = clients[ready_socket]

            for client_socket in clients:
                client_socket.send(user['header'] + user['message'] +
                                   data['header'] + data['message'])

    # Error handling
    for ready_socket in error_sockets:
        sockets.remove(ready_socket)
        del clients[ready_socket]
