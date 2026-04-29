import argparse
import os

import llm_layer
import scoreEngine
import sectionDetector
import textProcessor


def printReport(careerName, algorithmScore, scoreDetails, keywordList, foundSections):
    d = scoreDetails
    print("\n=== " + careerName + " ===")
    print("Rule-based score: " + str(algorithmScore) + "/100")
    secs = ", ".join(sorted(foundSections.keys())) if foundSections else "(none)"
    print("Sections detected: " + secs)
    print("Part scores - required:", d["requiredHits"], "preferred:", d["preferredHits"],
          "structure:", d["structureHits"], "bonus kw:", d["keywordHits"])
    j = ", ".join
    print("Missing - required skills:", j(d["missingRequiredSkills"]) or "none")
    print("Missing - preferred skills:", j(d["missingPreferredSkills"]) or "none")
    print("Missing - sections:", j(d["missingSections"]) or "none")
    print("Missing - bonus keywords:", j(d["missingBonusKeywords"]) or "none")
    print("Top keywords:", j(keywordList[:10]))
    print()


def listCareers(kbDir):
    for name in sorted(os.listdir(kbDir)):
        if name.endswith(".json"):
            print(name[: -5])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("resumePath", nargs="?")
    parser.add_argument("--career", default="software_engineering")
    parser.add_argument(
        "--kbDir",
        default=os.path.join(os.path.dirname(__file__), "knowledgeBases"),
    )
    parser.add_argument(
        "--list-careers",
        action="store_true",
        help="List career keys from JSON files in --kbDir and exit.",
    )
    parser.add_argument(
        "--use-llm",
        action="store_true",
        help="Second opinion via Ollama (--use-llm).",
    )
    args = parser.parse_args()

    if args.list_careers:
        listCareers(args.kbDir)
        raise SystemExit(0)

    if not args.resumePath:
        parser.error("resumePath is required unless you pass --list-careers")

    if not os.path.isfile(args.resumePath):
        print("File not found: " + args.resumePath)
        raise SystemExit(1)
    kbPath = scoreEngine.kbPathForCareer(args.career, args.kbDir)
    if not os.path.isfile(kbPath):
        print("KB not found: " + kbPath)
        raise SystemExit(1)

    with open(args.resumePath, "r", encoding="utf-8") as resumeFile:
        rawText = resumeFile.read()

    knowledgeBase = scoreEngine.loadKnowledgeBase(kbPath)
    _, filteredTokens = textProcessor.buildResumeWordSet(rawText)
    keywordList = textProcessor.extractKeywords(filteredTokens, topN=20)
    foundSections = sectionDetector.detectSections(rawText)
    algorithmScore, scoreDetails = scoreEngine.runAlgorithmScore(
        rawText, foundSections, knowledgeBase
    )

    careerName = knowledgeBase.get("careerName", args.career)
    printReport(careerName, algorithmScore, scoreDetails, keywordList, foundSections)

    if args.use_llm:
        result, err = llm_layer.run_llm_review(
            rawText, careerName, algorithmScore, scoreDetails
        )
        if err:
            print("LLM: " + err)
        else:
            llm_layer.print_llm_block(result)


if __name__ == "__main__":
    main()
