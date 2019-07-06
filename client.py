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

        self.room = None

        self.typing = ""

    def has_name(self):
        return self.username != ""
