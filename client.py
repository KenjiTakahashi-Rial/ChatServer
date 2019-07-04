#########################################
# Chat Server Client                    #
# GungHo engineering test               #
# by Kenji Takahashi-Rial               #
#########################################

import errno
import socket
import sys

IP_ADDRESS = socket.gethostname()
PORT = 1081

# Use a header to know how long a message will be
HEADER_LENGTH = 8

# Set up the client and connect
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client_socket.connect((IP_ADDRESS, PORT))

except Exception as e:
    print("Could not establish connection with the server")
    sys.exit()

client_socket.setblocking(False)


def send_message(message):
    """
    Description:
        Handles sending a message to the server
    Arguments:
        A message to send
    Return Value:
        True if the message sent successfully
        False if the message is blank
    """

    # Do not send blank messages
    if len(message.strip()) == 0:
        return False

    try:
        header = f"{len(message):<{HEADER_LENGTH}}"
        client_socket.send((header + message).encode('utf-8'))

        return True
    except Exception as e:
        print("Connection closed by the server")
        sys.exit()


def get_message():
    """
    Description:
        Handles getting a message from the server
    Arguments:
        None
    Return Value:
        The message received
        False if no messages to receive
    """

    try:
        header = client_socket.recv(HEADER_LENGTH)

        # If connection is aborted, there is no header
        if len(header) == 0:
            print("Connection closed by the server")
            sys.exit()

        head_len = int(header.decode('utf-8').strip())
        message = client_socket.recv(head_len).decode('utf-8')

        return "<= " + message

    # When there is no incoming data, EAGAIN and EWOULDBLOCK are thrown,
    # so return False for those, otherwise print an error and exit
    except IOError as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            print("Connection closed by the server")
            sys.exit()

        return False

    # Any other errors catch here
    except Exception as e:
        print("Connection closed by the server")
        sys.exit()


# Main client loop
while True:
    message = get_message()

    if message is not False:
        print(message)

    send_message(input("=> "))
