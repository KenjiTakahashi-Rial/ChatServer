#########################################
# server.py                             #
# The Server object and functions       #
# by Kenji Takahashi-Rial               #
#########################################

import socket as socket_module
import sys

import client

SOCKET_BUFFER = 4096

# Do not print backspace, arrow keys, function keys,
ILLEGAL_CHARS = ['\x08', '\x1b[A', '\x1b[B', '\x1b[C', '\x1b[D', '\x1bOP',
                 '\x1bOQ', '\x1bOR', '\x1bOS', '\x1b[15~', '\x1b[17~',
                 '\x1b[18~', '\x1b[19~', '\x1b[20~', '\x1b[21~', '\x1b[23~',
                 '\x1b[24~]', '\x1b[2~', '\x1b[1~', '\x1b[5~', '\x7f',
                 '\x1b[4~', '\x1b[6~', '\x1b[P']


class Server():

    def __init__(self, server_socket, rooms={}):
        self.socket = server_socket
        self.sockets = [server_socket]

        # A dictionary with the client socket as the key
        # and the client object as the value
        self.clients = {}

        # A dictionary with the client username as the key
        # and the client object as the value
        self.usernames = {}

        # A dictionary with the clients of the room as the key
        # and a list of client objects in the room as a value
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

    def send(self, data, client, prompt=True):
        """
        Description:
            Handles sending a data to a client
        Arguments:
            A Server object
            Data to send
            A client object to send a data to
        Return Value:
            True if the data sent successfully
            False if an error occurred
        """

        try:
            # Send the data
            client.socket.send((f"<= {data}\r\n").encode('utf-8'))

            if prompt:
                client.socket.send("=> ".encode('utf-8'))

            return True

        # Catch and display exceptions without crashing
        except Exception as e:
            print(f"\nsend() error: {e}\n")

            return False

    def receive(self, client):
        """
        Description:
            Handles receiving a data from a client
        Arguments:
            A Server object
            A client object to receive a data from
        Return Value:
            True if the client typed a message and hit enter
            None if the client hit enter on a blank message or has not
            hit enter yet
            False if an error occurred
        """

        try:
            data = client.socket.recv(SOCKET_BUFFER).decode('utf-8')

            client.typing += data

            # The user hit enter
            if client.typing[-1] == '\n':
                client.typing = client.typing[:-1]

                # For Windows remove the carriage return
                if client.typing[-1] == '\r':
                    client.typing = client.typing[:-1]

                    # Check for empty data
                    if len(client.typing) == 0:
                        client.socket.send("=> ".encode('utf-8'))

                        return None

                # Check for empty data
                if len(client.typing) == 0:
                    client.socket.send("\r\n=> ".encode('utf-8'))

                    return None

                # Non-empty data
                message = client.typing
                client.typing = ""

                return message

            return None

        # Catch and display exceptions without crashing
        except Exception as e:
            print(f"\nreceive() error: {e}\n")

            return False

    def connection_terminated(self, client):
        """
        Description:
            Prints a message that a client terminated their connection and
            removes the client from the server
        Arguments:
            A Server object
            A client whose connection was or is to be terminated
        Return Value:
            None
        """

        if client.has_name():
            print(f"\nConnection {client.address} terminated by client " +
                  f"{client.username}\n")

            del self.usernames[client.username]

        else:
            print(f"\nConnection {str_address} terminated by unnamed client\n")

        self.sockets.remove(client.socket)

        client.socket.close()

        del self.clients[client.socket]

    def initialize_client(self, client_socket):
        """
        Description:
            Gets the client data and stores it in the server
        Agruments:
            A Server object
            A client socket to initialize
        Return Value:
            A new client object
        """

        # New client object
        new_client = client.Client(client_socket)

        # Add user data to the server
        self.sockets.append(client_socket)
        self.clients[client_socket] = new_client

        # Prompt the user to enter a username
        self.send("Username?: ", new_client)

        print(f"\nNew connection: {new_client.address}\n")

        return new_client

    def set_username(self, client, username):
        """
        Descripton:
            Set the username for a client
            Cannot be empty, contain spaces, or identical to another username
        Arguments:
            A server object
            A client object to set the username of
            A proposed username
        Return Value:
            True if the username was set successfully
            False if the username is invalid or an error occurred
        """

        # Check username is not empty
        if len(username) == 0:
            self.send("Username cannot be empty", client, False)
            self.send("Username?: ", client)

            return False

        # Check username does not contain spaces
        if any([c.isspace() for c in username]):
            self.send("Username cannot contain spaces", client, False)
            self.send("Username?: ", client)

            return False

        # Check username is not taken
        if username in self.usernames:
            self.send(f"Sorry, {username} is taken", client, False)
            self.send("Username?: ", client)

            return False

        client.username = username
        self.usernames[username] = client

        self.send(f"Welcome, {username}!", client)

        print(f"\nClient at {client.address} set username to " +
              f"{client.username}\n")

        return True

    def process(self, data, client):
        """
        Description:
            Checks the sender of the data and carries out the
            appropriate functions whether it is a command or a message
        Arguments:
            A Server object
            A string of data to process
            The client object the data originated from
        Return Value:
            True if the data was processed successfully
            False if an error occurred
        """

        # Client has not set username yet
        if not client.has_name():
            return self.set_username(client, data)

        # Reroute to command function
        if data[0] == '/':
            if len(data) == 1 or data[1] != '/':
                return self.server_command(data, client)

            # User escaped / by using // so trim the leading /
            data = data[1:]

        # Client is not in a room
        if client.room is None:
            self.send("Message not sent - not in a room. " +
                      "Type /help for a list of commands.", client)

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
                        self.send(f"{client.username}: {data}", user)

                # Server sends a notification
                else:
                    if user not in except_users:
                        self.send(data, user)

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
                    "/private": self.private, "/p": self.private,
                    "/exit": self.client_exit, "/x": self.client_exit,
                    "/quit": self.client_exit, "/q": self.client_exit}

        try:
            return commands[cmd](args, client)

        # Incorrect command entered, show all valid commands
        except KeyError as e:
            valid_commands = ("Valid commands:\n\r" +
                              " * /rooms - See active rooms.\n\r" +
                              " * /join <room> - Join a room. Default: " +
                              "chat\n\r" +
                              " * /who <room> - See who is in a room. " +
                              "Default: current room \n\r" +
                              " * /leave - Leave your current room.\n\r" +
                              " * /private <user> <message> - Send a private " +
                              "message.\n\r" +
                              " * /quit - Disconnect from the server.\n\n\r" +
                              " * To use backslash without a command: //\n\r" +
                              " * Typing backslash with only the first " +
                              "letter of a command works as well\n\r" +
                              "End list.")

            self.send(valid_commands, client)

            return False

    def show_rooms(self, args, client):
        """
        Description:
            Display the active rooms
        Arguments:
            A Server object
            A list of arguments
            The client object that issued the command
        Return Value:
            True if the command was carried out
            False if an error occurred
        """

        self.send("Active rooms:", client, False)

        for room in self.rooms:
            self.send(f" * {room} ({len(self.rooms[room])})", client, False)

        self.send("End list.", client)

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
            The client object that issued the command
        Return Value:
            True if the command was carried out
            False if an error occurred
        """

        if client.room is not None:
            self.send(f"You are already in a room: {client.room}", client)

            return False

        if len(args) == 0:
            args.append("chat")

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
                self.send(f"Joined the room: {a}", client, False)

                # Show the client who else is in the room
                return self.who([], client)

        # Room doesn't exist
        self.send(f"No such room: {args[0]}", client)

        return False

    def who(self, args, client):
        """
        Description:
            Displays who is in the current room with the user
        Arguments:
            A Server object
            A list of arguments
            The client object that issued the command
        Return Value:
            True if the command was carried out
            False if an error occurred
        """

        # User not in a room
        if client.room is None:
            self.send("Not in a room.", client)

            return False

        # Iterate through users in room
        self.send(f"Users in: {client.room}", client, False)

        for user in self.rooms[client.room]:
            if user.username == client.username:
                self.send(f" * {user.username} (you)", client, False)
            else:
                self.send(f" * {user.username}", client, False)

        self.send("End list.", client)

        return True

    def leave(self, args, client, exit=False):
        """
        Description:
            Leaves the room that the user is currently in
        Arguments:
            A Server object
            A list of arguments
            The client object that issued the command
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
            # Don't print the leave message when exiting
            if not exit:
                self.send(f"Left the room: {client.room}", client)

            self.rooms[client.room].remove(client)
            client.room = None

            return True

        # Client is not in a room
        else:
            self.send("Not in a room.", client)

            return False

    def private(self, args, client):
        """
        Description:
            Sends a message to only the client and one other specified
            user
        Arguments:
            A Server object
            A list of arguments
            The client object that issued the command
        Return Value:
            True if the command was carried out
            False if an error occurred
        """

        if len(args) == 0:
            return self.send("Usage: /private <user> <message>", client)

        if args[0] == client.username:
            self.send("Cannot send private message to yourself", client)

            return False

        try:
            send_to = self.usernames[args[0]]

        except KeyError as E:
            self.send(f"User not found: {args[0]}", client)

            return False

        # No message to deliver, so do nothing
        if len(args) == 1:
            client.socket.send("=> ".encode('utf-8'))

            return True

        # Reconstruct message from args
        message = " ".join(args[1:])

        sent_to = self.send(f"{client.username} (private): {message}", send_to)
        sent_from = self.send(f"{client.username} (private): {message}",
                              client)

        return sent_to and sent_from

    def client_exit(self, args, client):
        """
        Description:
            Disconnects the client from the server
        Arguments:
            A Server object
            A list of arguments
            The client object that issued the command
        Return Value:
            True if the command was carried out
            False if an error occurred
        """

        # Remove the client from any rooms
        if client.room is not None:
            if not self.leave([], client, True):
                return False

        # Then disconnect the client
        self.send("Come again soon!", client, False)
        self.connection_terminated(client)

        return True
