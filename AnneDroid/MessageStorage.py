import datetime
import sqlite3

from Message import Message
from Errors import StorageError




class MessageStorage:
    SQL_CREATE_MESSAGES_TABLE = """CREATE TABLE IF NOT EXISTS messages (
                                        id integer PRIMARY KEY,
                                        author text NOT NULL,
                                        message text NOT NULL,
                                        channel text NOT NULL,
                                        date text NOT NULL
                                    );"""

    SQL_INSERT_MESSAGE = """INSERT INTO messages(author,message,channel,date)
                            VALUES(?,?,?,?) """

    def __init__(self, filename):
        try:
            self.Connection = sqlite3.connect(filename)
            if self.Connection is not None:
                c = self.Connection.cursor()
                c.execute(self.SQL_CREATE_MESSAGES_TABLE)
        except sqlite3.Error as e:
            raise StorageError(e)

    def insert_message(self, message):
        if self.Connection is not None:
            if isinstance(message, Message):
                try:
                    c = self.Connection.cursor()

                    m = (message.Author, message.Message, message.Channel, message.Date)
                    c.execute(self.SQL_INSERT_MESSAGE, m)
                    self.Connection.commit()

                    return c.lastrowid
                except Exception as e:
                    raise StorageError(e)

            else:
                raise StorageError()

    def select_messages(self):
        if self.Connection is not None:
            c = self.Connection.cursor()
            c.execute("SELECT * FROM messages")

            rows = c.fetchall()
            for r in rows:
                yield Message(r[1], r[2], r[3])

    def select_messages_by_author(self, author):
        if self.Connection is not None:
            c = self.Connection.cursor()
            c.execute("SELECT * FROM messages WHERE author=?", (author,))

            rows = c.fetchall()
            for r in rows:
                yield Message(r[1], r[2], r[3], r[4])

    def select_messages_by_channel(self, channel):
        if self.Connection is not None:
            c = self.Connection.cursor()
            c.execute("SELECT * FROM messages WHERE channel=?", (channel,))

            rows = c.fetchall()
            for r in rows:
                yield Message(r[1], r[2], r[3], r[4])