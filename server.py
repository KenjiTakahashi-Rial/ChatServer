#########################################
# server.py                             #
# The Server object and functions       #
# by Kenji Takahashi-Rial               #
#########################################

import socket as socket_module
import sys

import client
import room

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

        # A list of the sockets in the server
        self.sockets = [server_socket]

        # A dictionary with the client socket as the key
        # and the client object as the value
        self.clients = {}

        # A dictionary with the client username as the key
        # and the client object as the value
        self.usernames = {}

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

    def send(self, data, client):
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
            client.socket.send((f"\r<= {data}\r\n").encode('utf-8'))

            # Re-print the message the user was just typing to make it
            # seem like the user was not interruped
            # Only works on Windows because Linux and OS X don't send
            # continuous data!
            client.socket.send(("=> " + client.typing).encode('utf-8'))

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
                        client.socket.send("\r=> ".encode('utf-8'))

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

        no_errors = True

        # Check username is not empty
        if len(username) == 0:
            self.send("Username cannot be empty", client)

            no_errors = False

        # Check username does not contain spaces
        if any([c.isspace() for c in username]):
            self.send("Username cannot contain spaces", client)

            no_errors = False

        # Check username is not taken
        if username in self.usernames:
            self.send(f"Sorry, {username} is taken", client)

            no_errors = False

        if no_errors:
            client.username = username
            self.usernames[username] = client

            self.send(f"Welcome, {username}!", client)

            print(f"\nClient at {client.address} set username to " +
                  f"{client.username}\n")

        else:
            self.send("Username?: ", new_client)

        return no_errors

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
                      "Type /help for a list of commands", client)

            return False

        # Normal data distribution
        # User sends a message to their room
        return self.distribute(data, [client.room.name], client)

    def distribute(self, data, rooms, client=None, except_users=[]):
        """
        Description:
            Distributes data to all users in a given room
        Arguments:
            A Server object
            Data to send
            A list of rooms name to send to
            The client object who sent the data (None means the server)
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

            for user in self.rooms[room].users:
                # User sends data
                if client is not None:
                    if user not in except_users:
                        send_user = client.username

                        # Tag user appropriately
                        if client.username == self.rooms[room].owner:
                            send_user += " (owner)"

                        if client.username in self.rooms[room].admins:
                            send_user += " (admin)"

                        self.send(f"{send_user}: {data}", user)

                # Server sends a message
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
                    "/create": self.create, "/c": self.create,
                    "/kick": self.kick, "/k": self.kick,
                    "/delete": self.delete, "/d": self.delete,
                    "/exit": self.client_exit, "/x": self.client_exit,
                    "/quit": self.client_exit, "/q": self.client_exit}

        # Incorrect command entered, show all valid commands
        if cmd not in commands:
            valid_commands = ("Valid commands:\n\r" +
                              " * /rooms - See active rooms\n\r" +
                              " * /join <room> - Join a room\n\r" +
                              " * /who <room> - See who is in a room " +
                              "Default: current room \n\r" +
                              " * /leave - Leave your current room\n\r" +
                              " * /private <user> <message> - Send a " +
                              "private message\n\r" +
                              " * /create <name> - Create a new room\n\r" +
                              " * /kick <user1> <user2> ... - Kick user(s) " +
                              "from your current room\n\r" +
                              " * /delete <name> - Delete a room\n\r" +
                              " * /quit - Disconnect from the server\n\n\r" +
                              " * To use backslash without a command: //\n\r" +
                              " * Typing backslash with only the first " +
                              "letter of a command works as well\n\r" +
                              "End list")

            self.send(valid_commands, client)

            return False

        # Run a command normally
        return commands[cmd](args, client)

    def show_rooms(self, args, client):
        """
        Description:
            Display the available rooms
        Arguments:
            A Server object
            A list of arguments
            The client object that issued the command
        Return Value:
            True if the command was carried out
            False if an error occurred
        """

        self.send("Available rooms:", client)

        for room in self.rooms:
            room_str = f" * {room} ({len(self.rooms[room].users)})"

            # Tag room appropriately
            if client.username in self.rooms[room].admins:
                room_str += " (admin)"

            if client.username == self.rooms[room].owner:
                room_str += " (owner)"

            if client.room == self.rooms[room]:
                room_str += " (current)"

            self.send(room_str, client)

        self.send("End list", client)

        return True

    def join(self, args, client):
        """
        Description:
            Puts the user in a room
        Arguments:
            A Server object
            A list of arguments
            The client object that issued the command
        Return Value:
            True if the command was carried out
            False if an error occurred
        """

        if client.room is not None:
            self.send(f"You are already in a room: {client.room.name}", client)

            return False

        if len(args) == 0:
            self.send("Usage: /join <room>", client)

            return False

        if len(args) > 1:
            self.send("Room name cannot contain spaces", client)

            return False

        # Add the username to the rooms dictionary
        # and the room to the client object
        if args[0] in self.rooms:
            self.rooms[args[0]].users.append(client)
            client.room = self.rooms[args[0]]

            # Tag user appropriately
            join_user = client.username
            if client.username == self.rooms[args[0]].owner:
                join_user += " (owner)"

            if client.username in self.rooms[args[0]].admins:
                join_user += " (admin)"

            # Notify other users that a new user has joined
            self.distribute(f"{join_user} joined the room", [args[0]],
                            None, [client])

            # Notify the user that they joined the room
            self.send(f"Joined the room: {args[0]}", client)

            # Show the client who else is in the room
            return self.who([], client)

        # Room doesn't exist
        self.send(f"Room does not exist: {args[0]}", client)

        return False

    def who(self, args, client):
        """
        Description:
            Displays who is in a room
            No arguments defaults to the user's current room
        Arguments:
            A Server object
            A list of arguments
            The client object that issued the command
        Return Value:
            True if the command was carried out
            False if an error occurred
        """

        # Multiple arguments
        if len(args) > 1:
            self.send("Room name cannot contain spaces", client)

            return False

        # Default to current room
        if len(args) == 0:
            # User not in a room
            if client.room is None:
                self.send("Not in a room", client)

                return False

            args.append(client.room.name)

        # Room doesn't exist
        if args[0] not in self.rooms:
            self.send(f"Room does not exist: {args[0]}", client)

            return False

        # Room is empty
        if len(self.rooms[args[0]].users) == 0:
            self.send(f"No users in: {args[0]}", client)

            return True

        # Iterate through users in room
        self.send(f"Users in: {args[0]} ({len(self.rooms[args[0]].users)})",
                  client)

        for user in self.rooms[args[0]].users:
            who_user = user.username

            # Tag user appropriately
            if user.username == self.rooms[args[0]].owner:
                who_user += " (owner)"

            if user.username in self.rooms[args[0]].admins:
                who_user += " (admin)"

            if user.username == client.username:
                who_user += " (you)"

            self.send(f" * {who_user}", client)

        self.send("End list", client)

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

        # Client is not in a room
        if client.room is None:
            self.send("Not in a room", client)

            return False

        leave_user = client.username
        # Tag user appropriately
        if client.username == client.room.owner:
            leave_user += " (owner)"

        if client.username in client.room.admins:
            leave_user += " (admin)"

        self.distribute(f"{leave_user} left the room", [client.room.name],
                        None, [client])

        # Don't print the leave message when exiting
        if not exit:
            self.send(f"Left the room: {client.room.name}", client)

        client.room.users.remove(client)
        client.room = None

        return True

    def private(self, args, client):
        """
        Description:
            Sends a message to only the client and one other user
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

        if args[0] not in usernames:
            self.send(f"User not found: {args[0]}", client)

            return False

        send_to = self.usernames[args[0]]

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

    def create(self, args, client):
        """
        Description:
            Create a new room
        Arguments:
            A Server object
            A list of arguments
            The client object that issued the command
        Return Value:
            True if the command was carried out
            False if an error occurred
        """

        if len(args) == 0:
            self.send("Usage: /create <name>", client)

            return False

        if len(args) > 1:
            self.send("Room name cannot contain spaces", client)

            return False

        if args[0] in self.rooms:
            self.send(f"Room already exists: {args[0]} ", client)

            return False

        self.rooms[args[0]] = room.Room(args[0], client)

        self.send(f"You created a room: {args[0]}", client)

        return True

    def kick(self, args, client):
        """
        Description:
            Kick one or more users from a room
            Must have adminship or ownership
        Arguments:
            A Server object
            A list of arguments
            The client object that issued the command
        Return Value:
            True if the command was carried out
            False if an error occurred
        """

        if len(args) == 0:
            self.send("Usage: /kick <user1> <user2> ...", client)

            return False

        if client.room is None:
            self.send("Not in a room", client)

            return False

        # Check priviliges
        if client.username != client.room.owner:
            if client.username not in client.room.admins:
                self.send("Insufficient priviliges to kick from: " +
                          client.room, client)

                return False

        no_errors = True

        for username in args:

            if username not in self.usernames:
                self.send(f"User does not exist: {username}", client)

                no_errors = False
                continue

            # Get user object
            user = self.usernames[username]

            if user not in client.room.users:
                self.send(f"User not in room: {username}", client)

                no_errors = False
                continue

            # Must be owner to kick admin
            if username in client.room.admins:
                if client.username != room.owner:
                    self.send("Insufficient priviliges to kick admin: " +
                              f"{username}", client)

                    no_errors = False
                    continue

            # Owner cannot be kicked
            if username == client.room.owner:
                self.send(f"Cannot kick owner from room: {client.room.owner}",
                          client)

                no_errors = False
                continue

            # Do not allow users to kick themselves
            if username == client.username:
                self.send("Cannot kick self from room", client)

                no_errors = False
                continue

            # Actually remove the user
            user.room = None
            user.typing = ""
            client.room.users.remove(user)

            # Notify all parties that a user was kicked
            self.send(f"You were kicked from the room: {client.room.name}",
                      user)

            self.send(f"Kicked user: {username}", client)

            self.distribute(f"{username} was kicked from the room",
                            [client.room.name], None, [client])

        return no_errors

    def delete(self, args, client):
        """
        Description:
            Delete a room
            Must have ownership
        Arguments:
            A Server object
            A list of arguments
            The client object that issued the command
        Return Value:
            True if the command was carried out
            False if an error occurred
        """

        if len(args) == 0:
            self.send("Usage: /delete <name>", client)

            return False

        if len(args) > 1:
            self.send("Room name cannot contain spaces", client)

            return False

        if args[0] not in self.rooms:
            self.send(f"Room does not exist {args[0]}", client)

            return False

        if client.username != self.rooms[args[0]].owner:
            self.send(f"Insufficient priviliges to delete: {args[0]}", client)

            return False

        # Get the room object
        room = self.rooms[args[0]]

        # Try to kick all users in the room except the owner
        kick_args = []
        for user in room.users:
            if user.username != room.owner:
                kick_args.append(user.username)

        if not self.kick(kick_args, client):
            self.send(f"Failed to kick all users", client)

            return False

        # Lastly, remove self
        if client.room == room:
            client.room = None
            client.typing = ""
            room.users.remove(client)

        del self.rooms[args[0]]

        self.send(f"Deleted room: {args[0]}", client)

        return True

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
        client.socket.send("Come again soon!\n\r".encode('utf-8'))
        self.connection_terminated(client)

        return True
