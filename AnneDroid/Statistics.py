import nltk
import codecs

from HanTa import HanoverTagger as ht

class Statistics:
    def __init__(self, messageStorage):
        self.MessageStorage = messageStorage
        self.Tagger = ht.HanoverTagger('morphmodel_ger.pgz')

        nltk.download('punkt')

    def message_length_stats(self, mdbChannel):
        replyMessage = "\n"

        channelMessages = self.MessageStorage.select_messages_by_channel(mdbChannel)

        count = 0
        userWordCountDict = {}
        for m in channelMessages:
            count += 1
            if (m.Author in userWordCountDict.keys()):
                userWordCountDict[m.Author] += len(m.Message)
            else:
                userWordCountDict[m.Author] = len(m.Message)

        listOfTuples = sorted(userWordCountDict.items(), reverse=True, key=lambda x: x[1])

        for tup in listOfTuples:
            replyMessage += tup[0] + "\t:\t" + str(tup[1]) + "\n"

        return replyMessage

    def message_most_common_nouns(self, mdbChannel, num_of_nouns=5, language='german'):
        replyMessage = "\n"

        channelMessages = self.MessageStorage.select_messages_by_channel(mdbChannel)

        nouns = []
        for m in channelMessages:
            words = nltk.word_tokenize(m.Message, language=language)
            try:
                tags = self.Tagger.tag_sent(words, taglevel=3)
                for tag in tags:
                    if tag[3] == "NN" or tag[3] == "NE":
                        nouns.append(tag[0])
            except:
                continue
           

        distribution = nltk.FreqDist(nouns)
        most_common_nouns = distribution.most_common(num_of_nouns)
        for n in most_common_nouns:
            replyMessage += n[0] + '\t:\t' + str(n[1]) + '\n'

        return replyMessage

    def random_quote(self, mdbChannel):
        import random
        replyMessage = "\n"
        channelMessages = self.MessageStorage.select_messages_by_channel(mdbChannel)

        quote = random.choice(list(channelMessages))

        replyMessage = "```" + quote.Author + ": " + quote.Message + "```"

        return replyMessage

