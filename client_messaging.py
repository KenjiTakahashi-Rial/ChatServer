#########################################
# client_messaging.py                   #
# The client messaging functions        #
# by Kenji Takahashi-Rial               #
#########################################

from server_messaging import HEADER_LENGTH
from client import connection_error


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

    # Do not send blank messages
    if len(message.strip()) == 0:
        return False

    try:
        header = f"{len(message):<{HEADER_LENGTH}}"
        client_socket.send((header + message).encode('utf-8'))

        return True
    except Exception as e:
        connection_error()

        return False


def get_message():
    """
    Description:
        Handles getting a message from the server
    Arguments:
        None
    Return Value:
        True if the message was received successfully
        False if no messages to receive or an error occurred
    """

    try:
        header = client_socket.recv(HEADER_LENGTH)

        # If connection was terminated, there is no header
        if len(header) == 0:
            connection_error()

        head_len = int(header.decode('utf-8').strip())
        message = client_socket.recv(head_len).decode('utf-8')

        return "<= " + message

    # When there is no incoming data, EAGAIN and EWOULDBLOCK are thrown,
    # so return False for those, otherwise print an error and exit
    except IOError as e:
        if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
            connection_error()

        return False

    # Any other errors catch here
    except Exception as e:
        connection_error()

        return False
