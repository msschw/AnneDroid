class Message:
    FORMAT = "%Y_%m_%d-%H:%M:%S"
    Author = ""
    Message = ""
    Date = ""

    def __init__(self, author, message, channel, date):
        self.Author = author
        self.Message = message
        self.Channel = channel
        self.Date = date
