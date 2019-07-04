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


def get_server_message():
    """
    Description:
        Handles getting messages from the server
    Arguments:
        None
    Return Value:
        A string of the message
    """

    header = client_socket.recv(HEADER_LENGTH)
    head_len = int(header.decode('utf-8').strip())
    message = client_socket.recv(head_len).decode('utf-8')

    return message


def get_user_message():
    """
    Description:
        Handles getting messages from a user
    Arguments:
        None
    Return Value:
        A string of the message
    """

    user_header = client_socket.recv(HEADER_LENGTH)
    user_length = int(user_header.decode('utf-8').strip())
    username = client_socket.recv(user_length).decode('utf-8')

    msg_header = client_socket.recv(HEADER_LENGTH)
    msg_len = int(msg_header.decode('utf-8').strip())
    message = client_socket.recv(msg_len).decode('utf-8')

    return f"{username}: {message}"


# Main client loop
while True:
    message = input("=> ")
    while True:
        print(get_server_message())
