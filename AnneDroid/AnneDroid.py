
import os

import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('ANNEDROID_TOKEN')
NAMESPACE = os.getenv('ANNEDROID_NAMESPACE')
KEYWORD_GOOGLE = os.getenv('ANNEDROID_KEYWORD_GOOGLE')
KEYWORD_HELP = os.getenv('ANNEDROID_KEYWORD_HELP')

client = discord.Client()

@client.event
async def on_message(message):
    if(message.author == client.user):
        return

    if(message.content.startswith(NAMESPACE)):
        tokens = message.content.split(' ')
        if(len(tokens) > 1):
            reply = ""
            if(tokens[1].lower() == KEYWORD_HELP):
                reply += KEYWORD_HELP + ":\n\n"
                reply += KEYWORD_GOOGLE + " " + "<query>" "\t:\t" + "perform google search"

            if(len(tokens) > 2):
                if(tokens[1].lower() == KEYWORD_GOOGLE):
                    try:
                        from googlesearch import search
                        searchresult = search(query=" ".join(tokens[2:]), start=0, stop=1)
                        reply += next(searchresult)
                    except ImportError:
                        print("no module named 'googlesearch' found")
                    except StopIteration:
                        print("insufficient results")
                    except:
                        print("could not handle search")

            if(len(reply) > 0):
                await message.channel.send(reply)

client.run(TOKEN)