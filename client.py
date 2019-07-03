#########################################
# Chat Server                           #
# GungHo engineering test               #
# by Kenji Takahashi-Rial               #
#########################################

import socket

IP_ADDRESS = socket.gethostname()
PORT = 1081

# Set up the server socket and start listening
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.bind((IP_ADDRESS, PORT))
server_socket.listen()

# DEBUG
print(f"Listening for connections on {IP_ADDRESS}:{PORT}...")

# Keep track of sockets and client information
sockets = [server_socket]
clients = {}
