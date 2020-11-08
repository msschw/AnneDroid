import os
import random
import datetime
import discord
import MessageStorage
import Statistics

from dotenv import load_dotenv
from Command import Command


def main():
    load_dotenv()
    TOKEN = os.getenv('ANNEDROID_TOKEN')

    ERROR_MESSAGE_COMMAND = "you are the weakest link"
    ERROR_MESSAGE = "i am the weakest link, goodbye!"

    MESSAGE_DATABASE = "messages.db"

    mdb = MessageStorage.MessageStorage(MESSAGE_DATABASE)
    statistics = Statistics.Statistics(mdb)
    client = discord.Client()

    @client.event
    async def on_message(message):
        from Errors import CommandError
        if message.author == client.user:
            return

        # log message
        mdbChannel = message.guild.name + ":" + message.channel.name
        mdb.insert_message(MessageStorage.Message(message.author.name, message.content, mdbChannel, datetime.datetime.now().strftime(MessageStorage.Message.FORMAT)))

        # check for stats
        if message.content.startswith(Command.KEYWORD_ACTIVE):
            try:
                tokens = message.content.split(' ')
                if len(tokens) > 1:
                    replyMessage = ""
                    if tokens[1] == "stats":
                        replyMessage = statistics.message_length_stats(mdbChannel)

                    if tokens[1] == "nouns":
                        replyMessage = statistics.message_most_common_nouns(mdbChannel)

                    if tokens[1] == "quote":
                        replyMessage = statistics.random_quote(mdbChannel)

                    if len(replyMessage) > 0:
                        if len(replyMessage.replace('\n', '')) > 0:
                            await message.channel.send(replyMessage)
                        return

            except Exception as e:
                print(ERROR_MESSAGE + "\t" + str(type(e)) + ": " + str(e))
                # print trace
                import traceback
                print(traceback.format_exc())
                pass


        # parse commands
        try:
            if message.content.startswith(Command.KEYWORD_ACTIVE):
                await set_dnd_state(message.author.name + "'s request")
                cmd = Command(message.content)
                reply = cmd.Execute()

                # send the reply
                if len(reply) > 0:
                    await message.channel.send(reply)

        except CommandError as e:
            # send the error
            await message.author.send(
                ERROR_MESSAGE_COMMAND + ", " + message.author.name + "!" + "\t" + str(type(e)) + ": " + str(e))
        except Exception as e:
            # do not send internal error
            # await message.channel.send(ERROR_MESSAGE + "\t" + str(type(e)) + ": " + str(e))
            # print instead
            print(ERROR_MESSAGE + "\t" + str(type(e)) + ": " + str(e))
            # print trace
            import traceback
            print(traceback.format_exc())
            pass
        finally:
            await set_idle_state()

    async def set_idle_state():
        await client.change_presence(activity=discord.Game(name="with herself"), status=discord.Status.online)

    async def set_dnd_state(message):
        await client.change_presence(activity=discord.Activity(name=message), status=discord.Status.dnd)

    @client.event
    async def on_ready():
        await set_idle_state()


    client.run(TOKEN)


if __name__ == "__main__":
    main()
