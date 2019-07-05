#########################################
# server.py                             #
# The Server object and functions       #
# by Kenji Takahashi-Rial               #
#########################################

import socket
import sys

import client


class Server():

    def __init__(self, server_socket, rooms={}, header_length=8):
        self.socket = server_socket
        self.sockets = [server_socket]

        # A dictionary with the client socket as the key
        # and the client object as the value
        self.clients = {}
        self.usernames = []

        # A dictionary with the clients of the room as the key
        # and a list of client objects in the room as a value
        self.rooms = rooms

        self.header_length = header_length

    def __str__(self):
        server_socket_str = f"server socket: {self.socket}\n\n"
        sockets_str = f"sockets: {self.sockets}\n\n"
        clients_str = f"clients: {self.clients}\n\n"
        rooms_str = f"rooms: {self.rooms}\n\n"
        header_str = f"header length: {self.header_length}\n\n"

        return (server_socket_str +
                sockets_str +
                clients_str +
                rooms_str +
                header_str)

    def send(self, message, client_socket):
        """
        Description:
            Handles sending a message to a client
        Arguments:
            A Server object
            A message to send
            A client socket to send a message to
        Return Value:
            True if the message sent successfully
            False if an error occurred
        """

        try:
            header = f"{len(message):<{self.header_length}}"
            client_socket.send((header + message).encode('utf-8'))

            return True

        # Exceptions indicate ungraceful client termanation
        except Exception as e:
            # self.connection_terminated(client_socket)
            print(f"\nsend() error: {e}\n")

            return False

    def receive(self, client_socket):
        """
        Description:
            Handles receiving a message from a client
        Arguments:
            A Server object
            A client socket to receive a message from
        Return Value:
            The message if it was received successfully
            True if a command was run successfully
            False if a connection was terminated or an error occurred
        """

        try:
            header = client_socket.recv(self.header_length)

            # If connection was terminated, there is no header
            if len(header) == 0:
                self.connection_terminated(client_socket)

                return False

            msg_len = int(header.decode('utf-8').strip())
            message = client_socket.recv(msg_len).decode('utf-8').strip()

            # Reroute to command function
            if message[0] == '/':
                if len(message) == 1 or message[1] != '/':
                    return self.server_command(message, client_socket)

                return message[1:]

            return message

        # Exceptions indicate ungraceful client termanation
        except Exception as e:
            # self.connection_terminated(client_socket)
            print(f"\nreceive() error: {e}\n")

            return False

    def server_command(self, input, client_socket):
        """
        Description:
            When a user precedes a message with backslash, it is
            interpreted as a command. This parses it.
        Arguments:
            A Server object
            A command to be executed (including backslash)
        Return Value:
            True if the command was carried out
            False if an error occurred
        """

        # Get the client object
        client = self.clients[client_socket]

        # Separate by whitespace to get arguments
        separated = input.split()
        cmd = separated[0]
        args = separated[1:]

        # Command definitions
        def rooms():
            self.send("Active rooms:", client_socket)

            for room in self.rooms:
                self.send(f" * {room} ({len(self.rooms[room])})",
                          client_socket)

            self.send("End list", client_socket)

            return True

        def join():
            if len(args) == 0:
                self.send(f"Usage: /join <room>", client_socket)

                return False

            if client.room is not None:
                self.send(f"You are already in a room: {client.room}",
                          client_socket)

                return False

            # Add the username to the rooms dictionary
            # and the room to the client object
            for a in args:
                if a in self.rooms:
                    self.rooms[a].append(client)
                    client.room = a

                    # Notify other users that a new user has joined
                    for user in self.rooms[a]:
                        if user.username != client.username:
                            self.send(f"{client.username} joined the room",
                                      user.socket)

                    # Notify the user that they joined the room
                    self.send(f"Joined the room: {a}", client_socket)

                    # Show the client who else is in the room
                    return who()

            # Room doesn't exist
            self.send(f"No such room \"{args[0]}\"", client_socket)

            return False

        def who():
            # User not in a room
            if client.room is None:
                self.send("Not in a room", client_socket)

                return False

            # Iterate through users in room
            self.send(f"Users in: {client.room}", client_socket)

            for user in self.rooms[client.room]:
                if user == client.username:
                    self.send(f" * {user.username} (you)", client_socket)
                else:
                    self.send(f" * {user.username}", client_socket)

            self.send("End list", client_socket)

            return True

        def leave():
            # Notify other users that a user has left
            for user in self.rooms[client.room]:
                if user.username != client.username:
                    self.send(f"{client.username} left the room",
                              user.socket)

            # Remove the userfrom the rooms dictionary
            # and the room from the client object
            if (client.room is not None):
                self.send(f"Left the room: {client.room}", client_socket)
                self.rooms[client.room].remove(client)
                client.room = None

                return True

            # Client is not in a room
            else:
                self.send("Not in a room", client_socket)

                return False

        def exit():
            # Remove the client from any rooms
            if client.room is not None:
                if not leave():
                    return False

            # Then disconnect the client
            self.send("Come again soon!", client_socket)
            self.connection_terminated(client_socket)

            return True

        # Command cases dictionary
        commands = {"/rooms": rooms, "/r": rooms,
                    "/join": join, "/j": join,
                    "/who": who, "/w": who,
                    "/leave": leave, "/l": leave,
                    "/exit": exit, "/x": exit,
                    "/quit": exit, "/q": exit}

        try:
            return commands[cmd]()

        # Incorrect command entered, show all valid commands
        except KeyError as e:
            self.send("Valid commands:", client_socket)
            self.send("{:<6} - See active rooms".format(" * /rooms"),
                      client_socket)
            self.send("{:<6} - Join a room".format(" * /join"),
                      client_socket)
            self.send("{:<6} - See who is in the current room"
                      .format(" * /who"), client_socket)
            self.send("{:<6} - Leave your current room".format(" * /leave"),
                      client_socket)
            self.send("{:<6} - Close your chat client".format(" * /exit"),
                      client_socket)
            self.send(" * To use backslash without a command: //",
                      client_socket)

            return False

    def initialize_user(self, client_socket):
        """
        Description:
            Gets the client data and stores it in the server
        Agruments:
            A Server object
            A client socket to initialize
            The client's address
        Return Value:
            A new client object
            False if connection was terminated or an error occurred
        """

        self.send("Welcome to the GungHo test chat server", client_socket)

        # Get the desired username
        while True:
            self.send("Username?: ", client_socket)
            username = self.receive(client_socket)

            # Connection terminated before name given
            if not username:
                return False

            # If username is taken, continue asking
            if username in self.usernames:
                self.send(f"Sorry, {username} is taken", client_socket)
                continue

            break

        # New client object
        new_client = client.Client(client_socket, username, self.header_length)

        # Add user data to the server
        self.sockets.append(client_socket)
        self.usernames.append(username)
        self.clients[client_socket] = new_client

        self.send(f"Welcome, {username}!", client_socket)

        return new_client

    def connection_terminated(self, client_socket):
        """
        Description:
            Prints a message that a client terminated their connection and
            removes the client from the server
        Arguments:
            A Server object
            A client socket whos connection was or is to be terminated
        Return Value:
            None
        """

        if client_socket in self.clients:
            ex_client = self.clients[client_socket]

            print(f"\nConnection {ex_client.address} terminated by client " +
                  f"{ex_client.username}\n")

            self.sockets.remove(ex_client.socket)
            self.usernames.remove(ex_client.username)
            del ex_client

        else:
            str_address = (f"{client_socket.getsockname()[0]}:" +
                           f"{client_socket.getsockname()[1]}")

            print(f"\nConnection {str_address} terminated by unnamed client\n")

        client_socket.close()
