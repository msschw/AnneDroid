import os

import discord
from dotenv import load_dotenv
from Command import Command


def main():
    load_dotenv()
    TOKEN = os.getenv('ANNEDROID_TOKEN')

    ERROR_MESSAGE_COMMAND = "you are the weakest link"
    ERROR_MESSAGE = "i am the weakest link, goodbye!"

    client = discord.Client()

    @client.event
    async def on_message(message):
        from Errors import CommandError
        if message.author == client.user:
            return

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
            await message.channel.send(
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
        await client.change_presence(activity=None, status=discord.Status.online)

    async def set_dnd_state(message):
        await client.change_presence(activity=discord.Activity(name=message), status=discord.Status.dnd)

    @client.event
    async def on_ready():
        await set_idle_state()


    client.run(TOKEN)


if __name__ == "__main__":
    main()
