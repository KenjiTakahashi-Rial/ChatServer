#########################################
# room.py                               #
# The Room object                       #
# by Kenji Takahashi-Rial               #
#########################################


class Room():

    def __init__(self, name, client):

        self.name = name

        if client is None:
            self.owner = " server "

        else:
            self.owner = client.username

        # List of admin usernames
        self.admins = []

        # List of client objects
        self.users = []

        # List of banned usernames
        self.banned = []

    def __str__(self):
        name_str = f"name: {self.name}\n\n"
        owner_str = f"owner: {self.owner}\n\n"
        admins_str = f"admins: {self.admins}\n\n"
        users_str = f"users: {self.users}\n\n"

        return (name_str +
                owner_str +
                admins_str +
                users_str)
