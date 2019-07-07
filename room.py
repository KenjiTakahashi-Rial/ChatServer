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

        self.users = []
