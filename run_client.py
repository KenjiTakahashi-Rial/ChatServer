#########################################
# run_client.py                         #
# The code to run the chat client       #
# by Kenji Takahashi-Rial               #
#########################################

import socket
import sys

import client


# INITIAL SETUP ####################################################


IP_ADDRESS = socket.gethostname()
PORT = 1081

HEADER_LENGTH = 8

# Set up the client and connect
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

try:
    client_socket.connect((IP_ADDRESS, PORT))

except Exception as e:
    print("Could not establish connection with the server.")
    sys.exit()

client_socket.setblocking(False)

# Create the Client object
chat_client = client.Client(client_socket, "", HEADER_LENGTH)


# MAIN CLIENT LOOP ##################################################


while True:
    message = chat_client.receive()

    if message is not False:
        print(message)

    chat_client.send(input("=> "))
