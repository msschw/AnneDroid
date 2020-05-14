from Errors import CommandError
from enum import Enum

class ActionType(Enum):
    none = 0 
    oneshot = 1
    restart = 2
    start = 3
    stop = 4
    toggle = 5

class CommandType(Enum):
    google = 1
    help = 0
    moogle = 2
    trivia = 3
    wiki = 4
    yt = 5

class Command(object):
    """command abstraction"""

    KEYWORD_ACTIVE="!ad"

    KEYWORD_COMMAND_GOOGLE="google"
    KEYWORD_COMMAND_HELP="help"
    KEYWORD_COMMAND_MOSCHUSGOOGLE="moogle"
    KEYWORD_COMMAND_WIKIPEDIA="wiki"
    KEYWORD_COMMAND_YOUTUBE="yt"


    KEYWORD_ACTION_ONESHOT="oneshot"
    KEYWORD_ACTION_RESTART="restart"
    KEYWORD_ACTION_START="start"
    KEYWORD_ACTION_STOP="stop"
    KEYWORD_ACTION_TOGGLE="toggle"

    ActionAssignment = {
        KEYWORD_ACTION_ONESHOT: ActionType.oneshot,
        KEYWORD_ACTION_RESTART: ActionType.restart,
        KEYWORD_ACTION_START: ActionType.start,
        KEYWORD_ACTION_STOP: ActionType.stop,
        KEYWORD_ACTION_TOGGLE: ActionType.toggle
    }

    CommandAssignment = {
        KEYWORD_COMMAND_GOOGLE: CommandType.google,
        KEYWORD_COMMAND_HELP: CommandType.help,
        KEYWORD_COMMAND_MOSCHUSGOOGLE: CommandType.moogle,
        KEYWORD_COMMAND_WIKIPEDIA: CommandType.wiki,
        KEYWORD_COMMAND_YOUTUBE: CommandType.yt
    }

    Action = ActionType.none
    Command = CommandType.help
    Query = ""

    def __init__(self, input):
        self.Parse(input)

    def Parse(self, input):
        if not isinstance(input, str):
            raise CommandError

        if not input.startswith(self.KEYWORD_ACTIVE):
            self.Action = ActionType.none
            return

        tokens = input.split(' ')

        # default assignment
        self.Command = CommandType.help
        self.Action = ActionType.oneshot

        # parse first token
        if len(tokens) > 1:
            if tokens[1] in self.CommandAssignment:
                self.Command = self.CommandAssignment[tokens[1]]
            else:
                raise CommandError("invalid command: " + tokens[1])
        
        # try parse second token
        firstQueryTokenPosition = 1
        if len(tokens) > 2:
            if tokens[2] in self.ActionAssignment:
                # action is specified
                self.Action = self.ActionAssignment[tokens[2]]
                firstQueryTokenPosition = 3
            else:
                # action unspecified, assume oneshot
                self.Action = ActionType.oneshot
                firstQueryTokenPosition = 2

        # try parse query
        if len(tokens) > firstQueryTokenPosition:
            self.Query = " ".join(tokens[firstQueryTokenPosition:])

    def Execute(self):
        if self.Action == ActionType.none:
            return ""

        if self.Command == CommandType.help:
            reply = self.KEYWORD_COMMAND_HELP + ":\n\n"
            reply += self.KEYWORD_COMMAND_GOOGLE + " " + "<query>" "\t:\t" + "perform google search\n"
            reply += self.KEYWORD_COMMAND_WIKIPEDIA + " " + "<query>" "\t:\t" + "perform wikipedia search\n"
            reply += self.KEYWORD_COMMAND_YOUTUBE + " " + "<query>" "\t:\t" + "perform youtube search\n"
            return reply

        elif (self.Command == CommandType.google) and (self.Query != ""):
            try:
                from googlesearch import search
                searchresult = search(query=self.Query, start=0, stop=1)
                return next(searchresult)
            except ImportError as ie:
                raise ie
            except StopIteration:
                raise CommandError("insufficient results")
                raise
            except:
                raise

        elif (self.Command == CommandType.moogle) and (self.Query != ""):
            return "!google " + self.Query

        elif (self.Command == CommandType.wiki) and (self.Query != ""):
            try:
                from wikipedia import search,page
                searchresult = search(query=self.Query)
                #just lookup the first one
                if(len(searchresult) > 0):
                    wikipage = page(searchresult[0])
                    return wikipage.title + ": " + wikipage.url
                else:
                    raise CommandError("insufficient results")
            except ImportError:
                raise ie
            except:
                raise

        elif((self.Command == CommandType.yt) and (self.Query != "")):
            try:
                from youtube_search import YoutubeSearch
                searchresult = YoutubeSearch(search_terms=self.Query, max_results=1)
                #just lookup the first one
                if(len(searchresult.videos) > 0):
                    return searchresult.videos[0]["title"] + ": " + "https://youtube.com" + searchresult.videos[0]["link"]
                else:
                    raise CommandError("insufficient results")
            except ImportError:
                raise ie
            except:
                raise

        else:
            raise CommandError("invalid command")