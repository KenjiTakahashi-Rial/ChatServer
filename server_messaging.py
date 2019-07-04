#########################################
# server_messaging.py                   #
# The server messaging functions        #
# by Kenji Takahashi-Rial               #
#########################################

from server import connection_terminated

# Use a header to know how long a message will be
HEADER_LENGTH = 8


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
        header = f"{len(message):<{HEADER_LENGTH}}"
        client_socket.send((header + message).encode('utf-8'))

        return True

    # Exceptions indicate ungraceful client termanation
    except Exception as e:
        connection_terminated(client_socket)

        return False


def get_message(client_socket):
    """
    Description:
        Handles receiving a message from a client
    Arguments:
        A client socket to get a message from
    Return Value:
        True if the message was received successfully
        False if a connection was terminated or an error occurred
    """

    try:
        header = client_socket.recv(HEADER_LENGTH)

        # If connection was terminated, there is no header
        if len(header) == 0:
            connection_terminated(client_socket)

            return False

        msg_len = int(header.decode('utf-8').strip())
        message = client_socket.recv(msg_len).decode('utf-8')

        return message

    # Exceptions indicate ungraceful client termanation
    except Exception as e:
        connection_terminated(client_socket)

        return False


def server_command(command, client_socket):
    """
    Description:
        When a user precedes a message with backslash, it is
        interpreted as a command. This parses it.
    Arguments:
        A command to be executed
    Return Value:
        True if the command was carried out
        False if there was an error
    """

    commands = {"rooms": rooms, "r": rooms,
                "join": join, "j": join,
                "leave": leave, "l": leave,
                "exit": exit, "x": exit,
                "quit": exit, "q": exit}

    def rooms():
        pass

    def join():
        pass

    def leave():
        pass

    def exit():
        connection_terminated(client_socket)
