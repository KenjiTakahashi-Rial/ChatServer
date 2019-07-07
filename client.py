#########################################
# client.py                             #
# The Client object                     #
# by Kenji Takahashi-Rial               #
#########################################

import socket


class Client():

    def __init__(self, client_socket,):
        self.socket = client_socket

        self.address = (f"{client_socket.getsockname()[0]}:" +
                        f"{client_socket.getsockname()[1]}")

        self.username = ""

        # The room object the client is currently in
        self.room = None

        # A buffer for a message before the client hits enter
        self.typing = ""

    def has_name(self):
        return self.username != ""
