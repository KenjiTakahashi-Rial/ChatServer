#########################################
# Chat Server                           #
# GungHo engineering test               #
# by Kenji Takahashi-Rial               #
#########################################

import socket

IP_ADDRESS = socket.gethostname()
PORT = 1081

# Use a header to know how long a message will be
HEADER_LENGTH = 8


def receive_data(client_socket):
    """
    Description:
        Handles receiving data from a client
    Arguments:
        A client socket to receive data from
    Return Value:
        A dictionary with the header and message data
    """

    header = client_socket.recv(HEADER_LENGTH)
    msg_len = int(header.decode('utf-8').strip())
    message = client_socket.recv(msg_len)

    return {'header': header, 'message': message}


# Set up the server socket and start listening
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((IP_ADDRESS, PORT))
server_socket.listen()

# DEBUG
print(f"Listening for connections on {IP_ADDRESS}:{PORT}...")

# Keep track of sockets and client information
sockets = [server_socket]
clients = {}
