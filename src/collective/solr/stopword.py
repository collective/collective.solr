import re

from collective.solr.utils import getConfig

reLine = re.compile(r"^\s*([A-Za-zÀ-ÖØ-öø-ÿ]*)")

raw = None
raw_case_insensitive = None
cooked = None


def parseStopwords(stopwords, stopwords_case_insensitive):
    return list(
        map(
            lambda word: word.lower() if stopwords_case_insensitive else word,
            filter(
                lambda word: word,
                map(lambda line: reLine.match(line).group(1), stopwords.splitlines()),
            ),
        )
    )


def getStopWords(config):
    global raw
    global cooked
    global raw_case_insensitive
    config = config or getConfig()
    stopwords = getattr(config, "stopwords", "") or ""
    stopwords_case_insensitive = getattr(config, "stopwords_case_insensitive", False)
    if (
        cooked is None
        or raw is not stopwords
        or raw_case_insensitive != stopwords_case_insensitive
    ):
        raw = stopwords
        raw_case_insensitive = stopwords_case_insensitive
        cooked = parseStopwords(raw, stopwords_case_insensitive)
    return cooked


def isStopWord(term, config):
    stopwords_case_insensitive = getattr(config, "stopwords_case_insensitive", False)
    stopwords = getStopWords(config)
    return (term.lower() if stopwords_case_insensitive else term) in stopwords
