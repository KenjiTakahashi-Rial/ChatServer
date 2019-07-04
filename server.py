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


def send_message(message, client_socket):
    """
    Description:
        Handles sending a message to a client
    Arguments:
        A message to send
        A client socket to send a message to
    Return Value:
        True if the message sent successfully
        False if an error occurred
    """

    try:
        header = "{len(message):<{HEADER_LENGTH}}"
        client_socket.send((header + message).encode('utf-8'))

        return True

    except Exception as e:
        print(f"Error: {e}")
        return False


def get_message(client_socket):
    """
    Description:
        Handles receiving a message from a client
    Arguments:
        A client socket to get a message from
    Return Value:
        The message received
        False if an error occurred
    """

    try:
        header = client_socket.recv(HEADER_LENGTH)
        msg_len = int(header.decode('utf-8').strip())
        message = client_socket.recv(msg_len).decode('utf-8')

        return message

    except Exception as e:
        print(f"Error: {e}")
        return False


def initialize_user(client_socket):
    """
    Description:
        Gets the client data and stores it in the server
    Agruments:
        A client socket to initialize
    Return Value:
        The client's chosen username
    """

    # Check if a username is already in use and keep asking until
    # a valid username is given
    while True:
        send_message("Username?: ", client_socket)

        username = get_message(client_socket)
        print(username)

        if username in usernames:
            name_taken(f"Sorry, {username} is taken\n", client_socket)
            continue

        break

    sockets.append(client_socket)
    clients[client_socket] = username
    usernames[username] = client_socket

    send_message(f"Welcome, {username}!", client_socket)

    return username


# Main server loop
while True:
    # Get the ready sockets
    read_sockets, write_sockets, error_sockets = (
        select.select(sockets, [], sockets))

    for ready_socket in read_sockets:
        # New connection
        if ready_socket == server_socket:
            client_socket, client_address = server_socket.accept()

            send_message("Welcome to the GungHo chat server\n", client_socket)

            new_user = initialize_user(client_socket)

            print(f"\nNew connection: {client_address[0]}:{client_address[1]}",
                  f", Username: {new_user}\n")

        # Get a message and distribute to clients
        else:
            message = get_message(ready_socket)
            username = clients[ready_socket]

            for client_socket in clients:
                send_message("{username}: {message}", client_socket)

    # Error handling
    for ready_socket in error_sockets:
        sockets.remove(ready_socket)
        del clients[ready_socket]
