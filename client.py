#########################################
# client.py                             #
# The Client object and functions       #
# by Kenji Takahashi-Rial               #
#########################################

import errno
import socket
import sys


class Client():

    def __init__(self, socket, username="", header_length=8):
        self.socket = socket

        str_address = (f"{socket.getsockname()[0]}:" +
                       f"{socket.getsockname()[1]}")
        self.address = str_address

        self.username = username
        self.room = None
        self.header_length = header_length

    def send(self, message):
        """
        Description:
            Handles sending a message to the server
        Arguments:
            A Client object
            A message to send
        Return Value:
            True if the message sent successfully
            False if the message is blank or an error occurred
        """

        # Do not send blank messages
        if len(message.strip()) == 0:
            return False

        try:
            header = f"{len(message):<{self.header_length}}"
            self.socket.send((header + message).encode('utf-8'))

            return True

        except Exception as e:
            self.connection_error()

            return False

    def receive(self):
        """
        Description:
            Handles receiving a message from the server
        Arguments:
            A Client object
        Return Value:
            True if the message was received successfully
            False if no messages to receive or an error occurred
        """

        try:
            header = self.socket.recv(self.header_length)

            # If connection was terminated, there is no header
            if len(header) == 0:
                self.connection_error()

            head_len = int(header.decode('utf-8').strip())
            message = self.socket.recv(head_len).decode('utf-8')

            return "<= " + message

        # When there is no incoming data, EAGAIN and EWOULDBLOCK are thrown,
        # so return False for those, otherwise print an error and exit
        except IOError as e:
            if e.errno != errno.EAGAIN and e.errno != errno.EWOULDBLOCK:
                self.connection_error()

            return False

        # Any other errors catch here
        except Exception as e:
            self.connection_error()

            return False

    def connection_error(self):
        """
        Description:
            When a connection error occurs, the server most likely
            terminated the connection. This prints a message to the client
            and exits
        Arguments:
            A Client object
        Return Value:
            None
        """
        print("<= Connection terminated by the server.")
        sys.exit()
