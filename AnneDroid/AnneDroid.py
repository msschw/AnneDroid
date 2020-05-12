
import os

import discord
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('ANNEDROID_TOKEN')
NAMESPACE = os.getenv('ANNEDROID_NAMESPACE')
KEYWORD_GOOGLE = os.getenv('ANNEDROID_KEYWORD_GOOGLE')
KEYWORD_WIKIPEDIA = os.getenv('ANNEDROID_KEYWORD_WIKIPEDIA')
KEYWORD_HELP = os.getenv('ANNEDROID_KEYWORD_HELP')
ERROR_MESSAGE_COMMAND = "you are the weakest link"
ERROR_MESSAGE = "i am the weakest link, goodbye!"

client = discord.Client()

@client.event
async def on_message(message):
    from Errors import CommandError
    if(message.author == client.user):
        return

    try:
        # name calling
        if(message.author.name == 'Eniosan'):
            raise CommandError(message.author.name)

        # command handling
        if(message.content.startswith(NAMESPACE)):
            tokens = message.content.split(' ')
            reply = ""
            if(len(tokens) == 2):
                
                if(tokens[1].lower() == KEYWORD_HELP):
                    reply += KEYWORD_HELP + ":\n\n"
                    reply += KEYWORD_GOOGLE + " " + "<query>" "\t:\t" + "perform google search"
                    reply += KEYWORD_WIKIPEDIA + " " + "<query>" "\t:\t" + "perform wikipedia search"
                else:
                    raise CommandError("invalid command: " + message.content)

            elif(len(tokens) > 2):
                # KEYWORD_GOOGLE
                if(tokens[1].lower() == KEYWORD_GOOGLE):
                    try:
                        from googlesearch import search
                        searchresult = search(query=" ".join(tokens[2:]), start=0, stop=1)
                        reply += next(searchresult)
                    except ImportError as ie:
                        raise ie
                    except StopIteration:
                        raise CommandError("insufficient results")
                        raise
                    except:
                        raise
                # KEYWORD_WIKIPEDIA
                if(tokens[1].lower() == KEYWORD_WIKIPEDIA):
                    try:
                        from wikipedia import search,page
                        searchresult = search(query=" ".join(tokens[2:]))
                        #just lookup the first one
                        if(len(searchresult) > 0):
                            wikipage = page(searchresult[0])
                            reply += wikipage.title + ": " + wikipage.url

                    except ImportError:
                        raise ie
                    except:
                        raise

                else:
                    raise CommandError("unknown command: " + message.content)
            else:
                raise CommandError("invalid command: " + message.content)

            #send the reply
            if(len(reply) > 0):
                await message.channel.send(reply)

    except CommandError as e:
        #send the error
        await message.channel.send(ERROR_MESSAGE_COMMAND + ", " + message.author.name +"!" + "\t" + str(type(e)) + ": " + str(e))
    except Exception as e:
        #send internal error
        await message.channel.send(ERROR_MESSAGE + "\t" + str(type(e)) + ": " + str(e))

client.run(TOKEN)