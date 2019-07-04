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
        The message received
        False if an error occured
    """

    try:
        header = client_socket.recv(HEADER_LENGTH)
        head_len = int(header.decode('utf-8').strip())
        message = client_socket.recv(head_len).decode('utf-8')

        return message

    except Exception as e:
        print(f"Error: {e}")
        return False


def send_message(message):
    """
    Description:
        Handles sending a message to the server
    Arguments:
        A message to send
    Return Value:
        True if the message sent successfully
        False if the message is blank or an error occurred
    """

    if len(message.strip()) == 0:
        return False

    try:
        header = f"{len(message):<{HEADER_LENGTH}}"
        client_socket.send((header + message).encode('utf-8'))

        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


# Main client loop
while True:
    message = input("=> ")
    while True:
        if not send_message(message):
            break
