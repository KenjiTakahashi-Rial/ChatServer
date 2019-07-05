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

    def send(self, data, client_socket):
        """
        Description:
            Handles sending a data to a client
        Arguments:
            A Server object
            Data to send
            A client socket to send a data to
        Return Value:
            True if the data sent successfully
            False if an error occurred
        """

        try:
            header = f"{len(data):<{self.header_length}}"
            client_socket.send((header + data).encode('utf-8'))

            return True

        # Catch and display exceptions without crashing
        except Exception as e:
            print(f"\nsend() error: {e}\n")

            return False

    def receive(self, client_socket):
        """
        Description:
            Handles receiving a data from a client
        Arguments:
            A Server object
            A client socket to receive a data from
        Return Value:
            The data if it was received successfully
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
            data = client_socket.recv(msg_len).decode('utf-8').strip()

            return data

        # Catch and display exceptions without crashing
        except Exception as e:
            print(f"\nreceive() error: {e}\n")

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

    def process(self, data, client_socket):
        """
        Description:
            Checks whether the received data is a command or data to
            send and carries out the appropriate functions
        Arguments:
            A Server object
            String of data to process
            The client socket the data originated from
        Return Value:
            True if the data was processed successfully
            False if an error occurred
        """

        client = self.clients[client_socket]

        # Reroute to command function
        if data[0] == '/':
            if len(data) == 1 or data[1] != '/':
                return self.server_command(data, client)

            # User escaped / by using // so trim the leading /
            data = data[1:]

        # Client is not in a room
        if client.room is None:
            self.send("Message not sent - not in a room. " +
                      "Type /help for a list of commands.", client_socket)

            return False

        # Normal data distribution
        # User sends a message to their room
        return self.distribute(data, [client.room], client)

    def distribute(self, data, rooms, client=None, except_users=[]):
        """
        Description:
            Distributes data to all users in a given room
        Arguments:
            A Server object
            Data to send
            A list of rooms to send to
            The client object who sent the data
            A list of client objects not to send the message to
        Return Value:
            True if the data was distributed
            False if an error occurred
        """

        # No leading or trailing whitespace
        data = data.strip()

        # Don't send blank data
        # Must have a room to send to
        if len(data) == 0 or len(rooms) == 0:
            return False

        for room in rooms:
            # Some kind of error
            if room is None:
                return False

            for user in self.rooms[room]:
                # User sends data
                if client is not None:
                    if user not in except_users:
                        self.send(f"{client.username}: {data}", user.socket)

                # Server sends a notification
                else:
                    if user not in except_users:
                        self.send(data, user.socket)

        return True

    # Server commands ####################################################

    def server_command(self, input, client):
        """
        Description:
            When a user precedes data with backslash, it is interpreted
            as a command. This function reroutes to the corresponding
            command function
        Arguments:
            A Server object
            A command to be executed (including backslash)
            The client object that issued the command
        Return Value:
            True if the command was carried out
            False if an error occurred
        """

        # Separate by whitespace to get arguments
        separated = input.split()
        cmd = separated[0]
        args = separated[1:]

        # Command cases dictionary
        commands = {"/rooms": self.show_rooms, "/r": self.show_rooms,
                    "/join": self.join, "/j": self.join,
                    "/who": self.who, "/w": self.who,
                    "/leave": self.leave, "/l": self.leave,
                    "/exit": self.client_exit, "/x": self.client_exit,
                    "/quit": self.client_exit, "/q": self.client_exit}

        try:
            return commands[cmd](args, client)

        # Incorrect command entered, show all valid commands
        except KeyError as e:
            self.send("Valid commands:", client.socket)
            self.send("{:<6} - See active rooms.".format(" * /rooms"),
                      client.socket)
            self.send("{:<6} - Join a room.".format(" * /join"),
                      client.socket)
            self.send("{:<6} - See who is in the current room."
                      .format(" * /who"), client.socket)
            self.send("{:<6} - Leave your current room.".format(" * /leave"),
                      client.socket)
            self.send("{:<6} - Close the chat client.".format(" * /exit"),
                      client.socket)
            self.send(" * To use backslash without a command: //",
                      client.socket)

            return False

    def show_rooms(self, args, client):
        """
        Description:
            Display the active rooms
        Arguments:
            A Server object
            A list of arguments
            The client socket that issued the command
        Return Value:
            True if the command was carried out
            False if an error occurred
        """

        self.send("Active rooms:", client.socket)

        for room in self.rooms:
            self.send(f" * {room} ({len(self.rooms[room])})",
                      client.socket)

        self.send("End list.", client.socket)

        return True

    def join(self, args, client):
        """
        Description:
            Allows a user to join a room
            Adds the user to the rooms disctionary and adds the room
            to the client object
        Arguments:
            A Server object
            A list of arguments
            The client socket that issued the command
        Return Value:
            True if the command was carried out
            False if an error occurred
        """

        if len(args) == 0:
            self.send(f"Usage: /join <room>", client.socket)

            return False

        if client.room is not None:
            self.send(f"You are already in a room: {client.room}",
                      client.socket)

            return False

        # Add the username to the rooms dictionary
        # and the room to the client object
        for a in args:
            if a in self.rooms:
                self.rooms[a].append(client)
                client.room = a

                # Notify other users that a new user has joined
                self.distribute(f"{client.username} joined the room.", [a],
                                None, [client])

                # Notify the user that they joined the room
                self.send(f"Joined the room: {a}", client.socket)

                # Show the client who else is in the room
                return self.who([], client)

        # Room doesn't exist
        self.send(f"No such room: {args[0]}", client.socket)

        return False

    def who(self, args, client):
        """
        Description:
            Displays who is in the current room with the user
        Arguments:
            A Server object
            A list of arguments
            The client socket that issued the command
        Return Value:
            True if the command was carried out
            False if an error occurred
        """

        # User not in a room
        if client.room is None:
            self.send("Not in a room.", client.socket)

            return False

        # Iterate through users in room
        self.send(f"Users in: {client.room}", client.socket)

        for user in self.rooms[client.room]:
            if user.username == client.username:
                self.send(f" * {user.username} (you)", client.socket)
            else:
                self.send(f" * {user.username}", client.socket)

        self.send("End list.", client.socket)

        return True

    def leave(self, args, client):
        """
        Description:
            Leaves the room that the user is currently in
        Arguments:
            A Server object
            A list of arguments
            The client socket that issued the command
        Return Value:
            True if the command was carried out
            False if an error occurred
        """

        # Notify other users that a user has left
        self.distribute(f"{client.username} left the room.", [client.room],
                        None, [client])

        # Remove the userfrom the rooms dictionary
        # and the room from the client object
        if (client.room is not None):
            self.send(f"Left the room: {client.room}", client.socket)
            self.rooms[client.room].remove(client)
            client.room = None

            return True

        # Client is not in a room
        else:
            self.send("Not in a room.", client.socket)

            return False

    def client_exit(self, args, client):
        """
        Description:
            Exits the chat client
        Arguments:
            A Server object
            A list of arguments
            The client socket that issued the command
        Return Value:
            True if the command was carried out
            False if an error occurred
        """

        # Remove the client from any rooms
        if client.room is not None:
            if not self.leave([], client):
                return False

        # Then disconnect the client
        self.send("Come again soon!", client.socket)
        self.connection_terminated(client.socket)

        return True
