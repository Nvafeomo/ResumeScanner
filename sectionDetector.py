# Rough guess: if a line mentions a section word, count it. Not fancy and not always right.


def detectSections(resumeText):
    found = {}
    for lineIndex, line in enumerate(resumeText.splitlines()):
        low = line.strip().lower()
        if "education" in low:
            if "education" not in found:
                found["education"] = lineIndex
        if "experience" in low:
            if "experience" not in found:
                found["experience"] = lineIndex
        if "skill" in low:
            if "skills" not in found:
                found["skills"] = lineIndex
        if "project" in low:
            if "projects" not in found:
                found["projects"] = lineIndex
        if "summary" in low or "objective" in low:
            if "summary" not in found:
                found["summary"] = lineIndex
        if "certif" in low or "licens" in low:
            if "certifications" not in found:
                found["certifications"] = lineIndex
    return found
