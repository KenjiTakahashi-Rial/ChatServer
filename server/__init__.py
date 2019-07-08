###############################################################################
# __init__.py                                                                 #
# The server object definition                                                #
# by Kenji Takahashi-Rial                                                     #
###############################################################################


class Server():

    from .commands import command
    from .messaging import send, receive, connection_terminated, \
        initialize_client, set_username, process, distribute

    def __init__(self, server_socket, rooms={}):
        self.socket = server_socket

        self.address = (f"{server_socket.getsockname()[0]}:" +
                        f"{server_socket.getsockname()[1]}")

        # A list of all sockets connected to the server
        # including the server socket, itself
        self.sockets = [server_socket]

        # A dictionary with the client socket as the key
        # and the client object as the value
        # Only currently connected users should be in here
        self.clients = {}

        # A dictionary with the client username as the key
        # and the client object as the value
        # Only currently connected users should be in here
        self.usernames = {}

        # A dictionary with the username as the key
        # and the password as the value
        # All recoreded users (connected or disconnected)
        # should be in here
        self.passwords = {}

        # A dictionary with the name of the room as the key
        # and a room object as a value
        self.rooms = rooms

    def __str__(self):
        server_socket_str = f"server socket: {self.socket}\n\n"
        sockets_str = f"sockets: {self.sockets}\n\n"
        clients_str = f"clients: {self.clients}\n\n"
        rooms_str = f"rooms: {self.rooms}\n\n"

        return (server_socket_str +
                sockets_str +
                clients_str +
                rooms_str +
                header_str)
