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

        # Get room object
        room = self.rooms[room]

        # Tag room appropriately
        if client.username in room.admins:
            room_str += " (admin)"

        if client.username == room.owner:
            room_str += " (owner)"

        if client.room == room:
            room_str += " (current)"

        if client.username in room.banned:
            room_str += " (banned)"

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

    if args[0] not in self.rooms:
        self.send(f"Room does not exist: {args[0]}", client)

        return False

    # Get room object
    room = self.rooms[args[0]]

    if client.username in room.banned:
        self.send(f"You are banned from the room: {args[0]}", client)

        return False

    # Add the username to the rooms dictionary
    # and the room to the client object
    room.users.append(client)
    client.room = room

    # Tag user appropriately
    join_user = client.username
    if client.username == room.owner:
        join_user += " (owner)"

    if client.username in room.admins:
        join_user += " (admin)"

    # Notify other users that a new user has joined
    self.distribute(f"{join_user} joined the room", [args[0]],
                    None, [client])

    # Notify the user that they joined the room
    self.send(f"Joined the room: {args[0]}", client)

    # Show the client who else is in the room
    return who(self, [], client)


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

    if args[0] not in self.usernames:
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


def password(self, args, client):
    """
    Description:
        Set a password associated with a username
    Arguments:
        A Server object
        A list of arguments or an int/string depending on which stage
        of setting a password one is in
        The client object that issued the command
    Return Value:
        True if the command was carried out
        False if an error occurred
    """

    if isinstance(args, list) and len(args) > 0:
        self.send("Usage: /setpassword", client)

        client.setting_password = 0

        return False

    # Ask for old password or new password
    if client.setting_password == 0:
        if client.username in self.passwords:
            self.send("Old password:", client)

            client.setting_password = 1

        else:
            self.send("New password:", client)

            client.setting_password = 2

    elif client.setting_password == 1:
        if args != self.passwords[client.username]:
            self.send("Incorrect password", client)

            client.setting_password = 0

            return False

        else:
            self.send("New password:", client)

            client.setting_password = 2

    elif client.setting_password == 2:
        self.send("Confirm password:", client)

        client.setting_password = args

    else:
        if args != client.setting_password:
            self.send("Passwords did not match", client)

            client.setting_password = 0

            return False

        else:
            self.passwords[client.username] = args

            self.send("Password set", client)

            client.setting_password = 0

    return True


def new(self, args, client):
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
        self.send("Usage: /new <name>", client)

        return False

    if client.username not in self.passwords:
        self.send("Must set password to create room", client)

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


def admin(self, args, client):
    """
    Description:
        Give admin privileges to one or more users
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
        self.send("Usage: /admin <user1> <user2> ...", client)

        return False

    if client.room is None:
        self.send("Not in a room", client)

        return False

    # Check privileges
    if client.username != client.room.owner:
        self.send("Insufficient privileges to make admin in: " +
                  client.room.name, client)

        return False

    no_errors = True

    for username in args:

        if username not in self.passwords:
            if username not in self.usernames:
                self.send(f"User does not exist: {username}", client)

            else:
                self.send(f"User must set password to be admin: {username}",
                          client)

            no_errors = False
            continue

        # Get user object
        user = self.usernames[username]

        # Already admin
        if username in client.room.admins:
            self.send(f"User already admin: {username}", client)

            no_errors = False
            continue

        # Owner cannot be admin
        if username == client.username:
            self.send("You are the owner", client)

            no_errors = False
            continue

        # Promote the user
        client.room.admins.append(user.username)

        # Notify all parties that a user was kicked
        self.send(f"You were promoted to admin in: {client.room.name}",
                  user)

        self.send(f"Made admin: {username}", client)

        self.distribute(f"{username} was promoted to admin",
                        [client.room.name], None, [client, user])

    return no_errors


def cancel_admin(self, args, client):
    """
    Description:
        Revoke admin privileges for one or more users
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
        self.send("Usage: /canceladmin <user1> <user2> ...", client)

        return False

    if client.room is None:
        self.send("Not in a room", client)

        return False

    # Check privileges
    if client.username != client.room.owner:
        self.send("Insufficient privileges to cancel admin in: " +
                  client.room.name, client)

        return False

    no_errors = True

    for username in args:

        if username not in self.usernames and username not in self.passwords:
            self.send(f"User does not exist: {username}", client)

            no_errors = False
            continue

        if username not in client.room.admins:
            self.send(f"User not admin: {username}", client)

            no_errors = False
            continue

        client.room.admins.remove(username)

        # Notify all parties that a user was banned
        if username in self.usernames:
            self.send(f"You were demoted from admin in: {client.room.name}",
                      self.usernames[username])

        self.send(f"Revoked admin: {username}", client)

        self.distribute(f"{username} was demoted from admin",
                        [client.room.name], None, [client])

    return no_errors


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

    # Check privileges
    if client.username != client.room.owner:
        if client.username not in client.room.admins:
            self.send("Insufficient privileges to kick from: " +
                      client.room.name, client)

            return False

    no_errors = True

    for username in args:

        if username not in self.usernames and username not in self.passwords:
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
            if client.username != client.room.owner:
                self.send("Insufficient privileges to kick admin: " +
                          f"{username}", client)

                no_errors = False
                continue

        # Do not allow users to kick themselves
        if username == client.username:
            self.send("Cannot kick self", client)

            no_errors = False
            continue

        # Owner cannot be kicked
        if username == client.room.owner:
            self.send(f"Cannot kick owner: {client.room.owner}",
                      client)

            no_errors = False
            continue

        # Actually remove the user
        user.room = None
        user.typing = ""
        client.room.users.remove(user)

        # Notify all parties that a user was kicked
        self.send(f"You were kicked from: {client.room.name}",
                  user)

        self.send(f"Kicked user: {username}", client)

        self.distribute(f"{username} was kicked",
                        [client.room.name], None, [client])

    return no_errors


def ban(self, args, client):
    """
    Description:
        Ban one or more users from a room
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
        self.send("Usage: /ban <user1> <user2> ...", client)

        return False

    if client.room is None:
        self.send("Not in a room", client)

        return False

    # Check privileges
    if client.username != client.room.owner:
        if client.username not in client.room.admins:
            self.send("Insufficient privileges to ban from: " +
                      client.room.name, client)

            return False

    no_errors = True

    for username in args:

        if username not in self.usernames and username not in self.passwords:
            self.send(f"User does not exist: {username}", client)

            no_errors = False
            continue

        if username in client.room.banned:
            self.send(f"User already banned: {username}", client)

            no_errors = False
            continue

        # Must be owner to ban admin
        if username in client.room.admins:
            if client.username != client.room.owner:
                self.send("Insufficient privileges to ban admin: " +
                          f"{username}", client)

                no_errors = False
                continue

        # Do not allow users to ban themselves
        if username == client.username:
            self.send("Cannot ban self", client)

            no_errors = False
            continue

        # Owner cannot be banned
        if username == client.room.owner:
            self.send(f"Cannot ban owner: {client.room.owner}",
                      client)

            no_errors = False
            continue

        # Get user object
        user = self.usernames[username]

        # Remove the user first
        if user in client.room.users:
            user.room = None
            user.typing = ""
            client.room.users.remove(user)

        client.room.banned.append(user.username)

        # Notify all parties that a user was banned
        if username in self.usernames:
            self.send(f"You were banned from: {client.room.name}",
                      user)

        self.send(f"Banned user: {username}", client)

        self.distribute(f"{username} was banned",
                        [client.room.name], None, [client])

    return no_errors


def unban(self, args, client):
    """
    Description:
        Lift ban on a user from a room
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
        self.send("Usage: /unban <user1> <user2> ...", client)

        return False

    if client.room is None:
        self.send("Not in a room", client)

        return False

    # Check privileges
    if client.username != client.room.owner:
        if client.username not in client.room.admins:
            self.send("Insufficient privileges to unban in: " +
                      client.room.name, client)

            return False

    no_errors = True

    for username in args:

        if username not in self.usernames and username not in self.passwords:
            self.send(f"User does not exist: {username}", client)

            no_errors = False
            continue

        if username not in client.room.banned:
            self.send(f"User not banned: {username}", client)

            no_errors = False
            continue

        # Must be owner to lift ban on admin
        if username in client.room.admins:
            if client.username != client.room.owner:
                self.send("Insufficient privileges to unban admin: " +
                          f"{username}", client)

                no_errors = False
                continue

        client.room.banned.remove(username)

        # Notify all parties that a user was banned
        if username in self.usernames:
            self.send(f"Your were unbanned from: {client.room.name}",
                      self.usernames[username])

        self.send(f"Unbanned user: {username}", client)

        self.distribute(f"{username} was unbanned",
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

    if len(args) > 1:
        self.send("Room name cannot contain spaces", client)

        return False

    if len(args) == 0:
        args.append(client.room.name)

    if args[0] not in self.rooms:
        self.send(f"Room does not exist: {args[0]}", client)

        return False

    if client.username != self.rooms[args[0]].owner:
        self.send(f"Insufficient privileges to delete: {args[0]}", client)

        return False

    # Get the room object
    room = self.rooms[args[0]]

    for user in room.users:
        user.room = None
        user.typing = ""

        if user.username != room.owner:
            self.send(f"The room was deleted: {room.name}", user)

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


# Command cases dictionary
COMMANDS = {"/rooms": show_rooms, "/r": show_rooms,
            "/join": join, "/j": join,
            "/who": who, "/w": who,
            "/leave": leave, "/l": leave,
            "/private": private, "/p": private,
            "/setpassword": password, "/s": password,
            "/new": new, "/n": new,
            "/admin": admin, "/a": admin,
            "/canceladmin": cancel_admin, "/c": cancel_admin,
            "/kick": kick, "/k": kick,
            "/ban": ban, "/b": ban,
            "/unban": unban, "/u": unban,
            "/delete": delete, "/d": delete,
            "/exit": client_exit, "/x": client_exit,
            "/quit": client_exit, "/q": client_exit}

# Descriptions of the valid commands
VALID_COMMANDS = ("Valid commands:\n\r" +
                  " * /rooms - See active rooms\n\r" +
                  " * /join <room> - Join a room\n\r" +
                  " * /who <room> - See who is in a room. " +
                  "Default: current room \n\r" +
                  " * /leave - Leave your current room\n\r" +
                  " * /private <user> <message> - Send a " +
                  "private message\n\r" +
                  " * /setpassword - Set a password for your username\n\r" +
                  " * /new <name> - Create a new room\n\r" +
                  " * /admin <user1> <user2> ... - Make user(s) " +
                  " admins of your current room\n\r" +
                  " * /canceladmin <user1> <user2> ... - Revoke admin " +
                  "privileges for user(s)\n\r" +
                  " * /kick <user1> <user2> ... - Kick user(s) " +
                  "from your current room\n\r" +
                  " * /ban <user1> <user2> ... - Ban user(s) " +
                  "from your current room\n\r" +
                  " * /unban <user1> <user2> ... - Unban user(s) " +
                  "from your current room \n\r" +
                  " * /delete <name> - Delete a room. " +
                  "Default: current room\n\r" +
                  " * /quit - Disconnect from the server\n\r" +
                  " * Typing backslash with only the first " +
                  "letter of a command works as well\n\r" +
                  " * To use backslash without a command: //\n\r" +
                  "End list")


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

    # Incorrect command entered, show all valid commands
    if cmd not in COMMANDS:
        self.send(VALID_COMMANDS, client)

        return False

    # Run a command normally
    return COMMANDS[cmd](self, args, client)
