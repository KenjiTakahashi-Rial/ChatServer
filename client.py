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