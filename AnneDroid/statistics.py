import nltk

from HanTa import HanoverTagger as ht


class Statistics:
    def __init__(self, message_storage):
        self.MessageStorage = message_storage
        self.Tagger = ht.HanoverTagger("morphmodel_ger.pgz")

        nltk.download("punkt")

    def message_length_stats(self, mdb_channel):
        reply_message = "\n"

        channel_messages = self.MessageStorage.select_messages_by_channel(mdb_channel)

        count = 0
        user_word_count_dict = {}
        for m in channel_messages:
            count += 1
            if m.author in user_word_count_dict.keys():
                user_word_count_dict[m.author] += len(m.message)
            else:
                user_word_count_dict[m.author] = len(m.message)

        list_of_tuples = sorted(
            user_word_count_dict.items(), reverse=True, key=lambda x: x[1]
        )

        for tup in list_of_tuples:
            reply_message += tup[0] + "\t:\t" + str(tup[1]) + "\n"

        return reply_message

    def message_most_common_nouns(self, mdb_channel, num_of_nouns=5, language="german"):
        reply_message = "\n"

        channel_messages = self.MessageStorage.select_messages_by_channel(mdb_channel)

        nouns = []
        for m in channel_messages:
            words = nltk.word_tokenize(m.message, language=language)
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
            reply_message += n[0] + "\t:\t" + str(n[1]) + "\n"

        return reply_message

    def random_quote(self, mdb_channel):
        import random

        channel_messages = self.MessageStorage.select_messages_by_channel(mdb_channel)

        quote = random.choice(list(channel_messages))

        reply_message = "```" + quote.author + ": " + quote.message + "```"

        return reply_message
