###############################################################################
# commands.py                                                                 #
# The command functions for the server object                                 #
# by Kenji Takahashi-Rial                                                     #
###############################################################################

import socket

from room import Room


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
        return who(self, [], client)

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

    self.rooms[args[0]] = Room(args[0], client)

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

        # Do not allow users to kick themselves
        if username == client.username:
            self.send("Cannot kick self from room", client)

            no_errors = False
            continue

        # Owner cannot be kicked
        if username == client.room.owner:
            self.send(f"Cannot kick owner from room: {client.room.owner}",
                      client)

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

    if len(kick_args) != 0:
        if not kick(self, kick_args, client):
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
        if not leave(self, [], client, True):
            return False

    # Then disconnect the client
    client.socket.send("Come again soon!\n\r".encode('utf-8'))
    self.connection_terminated(client)

    return True


def command(self, input, client):
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
    commands = {"/rooms": show_rooms, "/r": show_rooms,
                "/join": join, "/j": join,
                "/who": who, "/w": who,
                "/leave": leave, "/l": leave,
                "/private": private, "/p": private,
                "/create": create, "/c": create,
                "/kick": kick, "/k": kick,
                "/delete": delete, "/d": delete,
                "/exit": client_exit, "/x": client_exit,
                "/quit": client_exit, "/q": client_exit}

    # Descriptions of the valid commands
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

    # Incorrect command entered, show all valid commands
    if cmd not in commands:
        self.send(valid_commands, client)

        return False

    # Run a command normally
    return commands[cmd](self, args, client)
