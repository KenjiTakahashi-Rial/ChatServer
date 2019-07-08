#########################################
# client.py                             #
# The Client object                     #
# by Kenji Takahashi-Rial               #
#########################################

import socket


class Client():

    def __init__(self, client_socket):
        self.socket = client_socket

        self.address = (f"{client_socket.getsockname()[0]}:" +
                        f"{client_socket.getsockname()[1]}")

        self.username = None

        # The room object the client is currently in
        self.room = None

        # A buffer for a message before the client hits enter
        self.typing = ""

        # Indicates whether the user is currently logging in
        self.logging_in = False

        # Indicates whether the user is setting a password
        # 0 if not settings a password
        # 1 if typing current password
        # 2 if typing new password
        # A string of the new password if confirming new password
        self.setting_password = 0

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
