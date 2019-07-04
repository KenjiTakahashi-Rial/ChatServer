#########################################
# Chat Server Client                    #
# GungHo engineering test               #
# by Kenji Takahashi-Rial               #
#########################################

import socket

IP_ADDRESS = socket.gethostname()
PORT = 1081

# Use a header to know how long a message will be
HEADER_LENGTH = 8

# Set up the client and connect
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((IP_ADDRESS, PORT))
client_socket.setblocking(False)


def get_message():
    """
    Description:
        Handles getting a message from the server
    Arguments:
        None
    Return Value:
        A string of the message
    """

    header = client_socket.recv(HEADER_LENGTH)
    head_len = int(header.decode('utf-8').strip())
    message = client_socket.recv(head_len).decode('utf-8')

    return message


# Main client loop
while True:
    message = input("=> ")
    while True:
        print(get_message())
