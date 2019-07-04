#########################################
# Chat Server Client                    #
# GungHo engineering test               #
# by Kenji Takahashi-Rial               #
#########################################

import errno
import socket
import sys

from client_messaging import *


# INITIAL SETUP ####################################################


IP_ADDRESS = socket.gethostname()
PORT = 1081

# Set up the client and connect
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client_socket.connect((IP_ADDRESS, PORT))

except Exception as e:
    print("Could not establish connection with the server")
    sys.exit()

client_socket.setblocking(False)


# FUNCTIONS ######################################################


def connection_error():
    """
    Description:
        When a connection error occurs, the server most likely
        terminated the connection. This prints a message to the client
        and exits
    Arguments:
        None
    Return Value:
        None
    """
    print("<= Connection terminated by the server")
    sys.exit()


# MAIN CLIENT LOOP ##################################################


while True:
    message = get_message()

    if message is not False:
        print(message)

    send_message(input("=> "))
