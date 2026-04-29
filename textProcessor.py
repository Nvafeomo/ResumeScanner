# Tokenize, drop stop words, count keywords.
import re
from collections import Counter

stopWords = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for", "of", "as",
    "by", "with", "from", "is", "are", "was", "were", "be", "been", "being", "it",
    "this", "that", "these", "those", "i", "my", "me", "we", "our", "you", "your",
    "he", "she", "they", "them", "his", "her", "their", "have", "has", "had", "do",
    "does", "did", "not", "no", "so", "if", "then", "than", "into", "about", "over",
    "also", "just", "all", "any", "can", "will", "would", "could", "should", "may",
    "com", "org", "edu", "www", "http", "https", "linkedin", "email",
}


def tokenizeText(rawText):
    return re.findall(r"[a-z0-9]+", rawText.lower())


def removeStopWords(tokens):
    out = []
    for token in tokens:
        if token.isdigit():
            continue
        if token not in stopWords and len(token) > 1:
            out.append(token)
    return out


def extractKeywords(filteredTokens, topN=25):
    counts = Counter(filteredTokens)
    return [word for word, _ in counts.most_common(topN)]


def buildResumeWordSet(rawText):
    tokens = tokenizeText(rawText)
    filtered = removeStopWords(tokens)
    return set(filtered), filtered
