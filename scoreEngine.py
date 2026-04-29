# Rule-based score: each JSON list earns part of 100 based on how many items match.
# Skills/keywords: whole-word / phrase match in raw resume text. Sections: detected section keys.
import json
import os
import re


def loadKnowledgeBase(jsonPath):
    with open(jsonPath, "r", encoding="utf-8") as file:
        return json.load(file)


def howManyHit(wantedList, bag):
    # bag is foundSections (dict of section names).
    missing = []
    hits = 0
    for w in wantedList:
        if w in bag:
            hits = hits + 1
        else:
            missing.append(w)
    return hits, missing


def _skillPattern(skillPhrase):
    parts = skillPhrase.lower().split()
    if len(parts) == 1:
        w = parts[0]
        frag = r"\b" + re.escape(w)
        if len(w) >= 3 and not w.endswith("s"):
            frag += r"s?"
        return frag + r"\b"
    return r"\b" + r"\s+".join(re.escape(p) for p in parts) + r"\b"


def howManyHitInText(wantedList, rawLower):
    missing = []
    hits = 0
    for w in wantedList:
        if re.search(_skillPattern(w), rawLower):
            hits = hits + 1
        else:
            missing.append(w)
    return hits, missing


def partPoints(hits, howManyWanted, maxPoints):
    if howManyWanted == 0:
        return maxPoints
    return (hits / howManyWanted) * maxPoints


def runAlgorithmScore(rawText, foundSections, knowledgeBase):
    weights = knowledgeBase.get("scoreWeights", {})
    maxRequired = float(weights.get("requiredSkills", 35))
    maxPreferred = float(weights.get("preferredSkills", 20))
    maxSections = float(weights.get("sections", 20))
    maxKeywords = float(weights.get("keywordOverlap", 25))

    requiredSkills = []
    for s in knowledgeBase.get("requiredSkills", []):
        requiredSkills.append(s.lower())

    preferredSkills = []
    for s in knowledgeBase.get("preferredSkills", []):
        preferredSkills.append(s.lower())

    expectedSections = knowledgeBase.get("expectedSections", ["education", "experience", "skills"])

    bonusKeywords = []
    for k in knowledgeBase.get("bonusKeywords", []):
        bonusKeywords.append(k.lower())

    rawLower = rawText.lower()
    h1, missingReq = howManyHitInText(requiredSkills, rawLower)
    h2, missingPref = howManyHitInText(preferredSkills, rawLower)
    h3, missingSec = howManyHit(expectedSections, foundSections)
    h4, missingKeys = howManyHitInText(bonusKeywords, rawLower)

    reqScore = partPoints(h1, len(requiredSkills), maxRequired)
    prefScore = partPoints(h2, len(preferredSkills), maxPreferred)
    secScore = partPoints(h3, len(expectedSections), maxSections)
    keyScore = partPoints(h4, len(bonusKeywords), maxKeywords)

    total = reqScore + prefScore + secScore + keyScore
    if total > 100.0:
        total = 100.0

    details = {
        "requiredHits": round(reqScore, 2),
        "preferredHits": round(prefScore, 2),
        "structureHits": round(secScore, 2),
        "keywordHits": round(keyScore, 2),
        "missingRequiredSkills": missingReq,
        "missingPreferredSkills": missingPref,
        "missingSections": missingSec,
        "missingBonusKeywords": missingKeys,
    }
    return round(total, 2), details


def kbPathForCareer(careerKey, baseDir):
    return os.path.join(baseDir, careerKey + ".json")
