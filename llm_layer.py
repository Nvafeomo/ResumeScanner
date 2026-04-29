# Ollama defaults: localhost:11434, model llama3.2. Env overrides OLLAMA_*.
import json
import os
import urllib.error
import urllib.request


_MAX_RESUME_CHARS = 12000

_DEFAULT_HOST = "http://127.0.0.1:11434"
_DEFAULT_MODEL = "llama3.2"

_SYSTEM = (
    "You compare a resume to a career profile. Output ONLY JSON with keys: "
    '"skills" (array of short strings for technologies/skills clearly stated '
    "in the resume), "
    '"score_note" (one sentence: does the rule-based score seem plausible?), '
    '"score_guess" (integer 0-100: your quick informal fit for this career). '
    "Do not invent skills not grounded in the resume."
)


def _truncate(text, limit=_MAX_RESUME_CHARS):
    if len(text) <= limit:
        return text
    return text[: limit].rsplit("\n", 1)[0] + "\n\n[...truncated...]"


def _misses_summary(details):
    parts = []
    req = details.get("missingRequiredSkills") or []
    pref = details.get("missingPreferredSkills") or []
    sec = details.get("missingSections") or []
    bonus = details.get("missingBonusKeywords") or []
    if req:
        parts.append("missing required: " + ", ".join(req[:12]))
    if pref:
        parts.append("missing preferred: " + ", ".join(pref[:12]))
    if sec:
        parts.append("missing sections: " + ", ".join(sec))
    if bonus:
        parts.append("missing bonus: " + ", ".join(bonus[:12]))
    return "; ".join(parts) if parts else "(nothing listed as missing)"


def _ollama_base():
    h = os.environ.get("OLLAMA_HOST", "").strip() or _DEFAULT_HOST
    return h.rstrip("/")


def _ollama_model():
    return os.environ.get("OLLAMA_MODEL", "").strip() or _DEFAULT_MODEL


def _parse_json_content(raw_text):
    raw_text = (raw_text or "").strip()
    try:
        return json.loads(raw_text)
    except json.JSONDecodeError:
        pass
    start = raw_text.find("{")
    end = raw_text.rfind("}")
    if start != -1 and end > start:
        try:
            return json.loads(raw_text[start : end + 1])
        except json.JSONDecodeError:
            pass
    raise json.JSONDecodeError("Expecting JSON object in model output", raw_text, 0)


def run_llm_review(raw_text, career_name, algorithm_score, score_details):
    base = _ollama_base()
    model_id = _ollama_model()
    chat_url = base + "/api/chat"

    user_body = (
        "Career target: "
        + career_name
        + "\nRule-based score from program: "
        + str(algorithm_score)
        + "/100\nWhat the rubric flagged as missing: "
        + _misses_summary(score_details)
        + "\n\nResume text:\n"
        + _truncate(raw_text)
    )

    payload_obj = {
        "model": model_id,
        "messages": [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": user_body},
        ],
        "stream": False,
        "format": "json",
        "options": {"temperature": 0.25},
    }
    payload = json.dumps(payload_obj).encode("utf-8")

    headers = {"Content-Type": "application/json"}
    api_key = os.environ.get("OLLAMA_API_KEY", "").strip()
    if api_key:
        headers["Authorization"] = "Bearer " + api_key

    req = urllib.request.Request(chat_url, data=payload, method="POST", headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            outer = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        hint = ""
        if exc.code == 401:
            hint = " Set OLLAMA_API_KEY if required."
        tail = exc.read().decode("utf-8", errors="replace")[:400]
        return None, (
            "Ollama HTTP "
            + str(exc.code)
            + ": "
            + tail.strip()
            + hint
        )
    except urllib.error.URLError as exc:
        return None, (
            "Cannot reach Ollama at "
            + chat_url
            + ". Start Ollama; pull model: ollama pull "
            + model_id
            + ". Details: "
            + str(exc.reason if hasattr(exc, "reason") else exc)
        )
    except TimeoutError:
        return None, "Ollama timed out."
    except json.JSONDecodeError:
        return None, "Ollama returned invalid HTTP JSON."

    content = ""
    msg = outer.get("message")
    if isinstance(msg, dict):
        content = msg.get("content") or ""

    try:
        data = _parse_json_content(content)
    except json.JSONDecodeError:
        return None, "Bad JSON from model."

    skills = data.get("skills") or []
    if isinstance(skills, list):
        skills = [str(s).strip() for s in skills if str(s).strip()]
    else:
        skills = []

    note = data.get("score_note") or ""
    if not isinstance(note, str):
        note = str(note)

    guess = data.get("score_guess")
    try:
        guess_int = int(guess)
        guess_int = max(0, min(100, guess_int))
    except (TypeError, ValueError):
        guess_int = None

    return {"skills": skills, "score_note": note.strip(), "score_guess": guess_int}, None


def print_llm_block(result):
    print("=== LLM layer (Ollama) ===")
    print(
        "Skills mentioned (from resume): " + ", ".join(result["skills"])
        if result["skills"]
        else "Skills mentioned (from resume): (none listed)"
    )
    if result["score_guess"] is not None:
        print("Informal LLM score guess: " + str(result["score_guess"]) + "/100")
    print("Note on rule-based score: " + (result["score_note"] or "(none)"))
    print()
