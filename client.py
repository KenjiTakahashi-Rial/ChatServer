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

    def __str__(self):
        socket_str = f"socket: {self.socket}\n\n"
        address_str = f"address: {self.address}\n\n"
        username_str = f"username: {self.username}\n\n"
        room_str = f"room: {self.room}\n\n"
        typing_str = f"typing: {self.typing}\n\n"

        return (socket_str +
                address_str +
                username_str +
                room_str +
                typing_str)
