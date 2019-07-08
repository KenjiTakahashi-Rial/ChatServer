###############################################################################
# messaging.py                                                                #
# The general messaging functions for the server object                       #
# by Kenji Takahashi-Rial                                                     #
###############################################################################

import socket

from client import Client
from .commands import password

SOCKET_BUFFER = 4096

# Do not print backspace, arrow keys, function keys,
ILLEGAL_CHARS = ['\x08', '\x1b[A', '\x1b[B', '\x1b[C', '\x1b[D', '\x1bOP',
                 '\x1bOQ', '\x1bOR', '\x1bOS', '\x1b[15~', '\x1b[17~',
                 '\x1b[18~', '\x1b[19~', '\x1b[20~', '\x1b[21~', '\x1b[23~',
                 '\x1b[24~]', '\x1b[2~', '\x1b[1~', '\x1b[5~', '\x7f',
                 '\x1b[4~', '\x1b[6~', '\x1b[P']


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

    #     return False


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

        if len(data) == 0:
            self.connection_terminated(client)

            return False

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

    # Catch connection forcibly closed
    except ConnectionResetError as e:
        print(f"\nreceive() error: {e}\n")

        self.connection_terminated(client)

        return False

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

    if client.username is not None:
        print(f"\nConnection {client.address} terminated by client " +
              f"{client.username}\n")

        if client.room is not None:
            client.room.users.remove(client)

        del self.usernames[client.username]

    else:
        print(f"\nConnection {client.address} terminated by unnamed client\n")

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
    new_client = Client(client_socket)

    # Add user data to the server
    self.sockets.append(client_socket)
    self.clients[client_socket] = new_client

    # Prompt the user to enter a username
    self.send("Username?: ", new_client)

    print(f"\nNew connection: {new_client.address}\n")

    return new_client


def login(self, client, password):
    """
    Description:
        Attempt to log in with a certain username
    Arguments:
        A Server object
        The client attempting to log in
    Return Value:
        True if the login was processed successfully
        False if an error occurred
    """

    # Check against saved password
    if self.passwords[client.username] != password:
        client.username = None
        client.logging_in = False

        self.send("Incorrect password", client)
        self.send("Username:", client)

        return False

    else:
        self.usernames[client.username] = client
        client.logging_in = False

        self.send(f"Welcome back, {client.username}!", client)

        return True


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
    elif any([c.isspace() for c in username]):
        self.send("Username cannot contain spaces", client)

        no_errors = False

    # Check if user has a password
    elif username in self.passwords:
        # Check if user already logged in
        if username in self.usernames:
            self.send(f"User already logged in: {username}", client)

            no_errors = False

    # Check username is not taken
    elif username in self.usernames:
        self.send(f"Sorry, {username} is taken", client)

        no_errors = False

    if no_errors:
        # Set the clients username for now
        client.username = username

        print(f"\nClient at {client.address} set username to " +
              f"{client.username}\n")

        if username in self.passwords:
            client.logging_in = True

            self.send("Password:", client)

        else:
            self.usernames[username] = client

            self.send(f"Welcome, {username}!", client)

    else:
        self.send("Username:", client)

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
    if client.username is None:
        return self.set_username(client, data)

    if client.logging_in:
        return login(self, client, data)

    if isinstance(client.setting_password, str) or client.setting_password > 0:
        return password(self, data, client)

    # Reroute to command function
    if data[0] == '/':
        if len(data) == 1 or data[1] != '/':
            return self.command(data, client)

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
