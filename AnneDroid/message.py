class Message:
    FORMAT = "%Y_%m_%d-%H:%M:%S"
    author = ""
    message = ""
    date = ""

    def __init__(self, author, message, channel, date):
        self.author = author
        self.message = message
        self.channel = channel
        self.date = date
