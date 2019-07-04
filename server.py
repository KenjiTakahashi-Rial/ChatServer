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
        self.clients = {}
        self.usernames = []
        self.rooms = rooms
        self.header_length = header_length

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
            self.connection_terminated(client_socket)

            return False

    def receive(self, client_socket):
        """
        Description:
            Handles receiving a message from a client
        Arguments:
            A Server object
            A client socket to receive a message from
        Return Value:
            True if the message was received successfully
            False if a connection was terminated or an error occurred
        """

        try:
            header = client_socket.recv(self.header_length)

            # If connection was terminated, there is no header
            if len(header) == 0:
                self.connection_terminated(client_socket)

                return False

            msg_len = int(header.decode('utf-8').strip())
            message = client_socket.recv(msg_len).decode('utf-8')

            return message

        # Exceptions indicate ungraceful client termanation
        except Exception as e:
            self.connection_terminated(client_socket)

            return False

    def server_command(self, command, client_socket):
        """
        Description:
            When a user precedes a message with backslash, it is
            interpreted as a command. This parses it.
        Arguments:
            A Server object
            A command to be executed
        Return Value:
            True if the command was carried out
            False if there was an error
        """

        commands = {"rooms": rooms, "r": rooms,
                    "join": join, "j": join,
                    "leave": leave, "l": leave,
                    "exit": exit, "x": exit,
                    "quit": exit, "q": exit}

        def rooms():
            pass

        def join():
            pass

        def leave():
            pass

        def exit():
            connection_terminated(client_socket)

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
