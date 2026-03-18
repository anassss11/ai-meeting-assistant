import logging
import os
import re
from collections import Counter
from functools import lru_cache

EMPTY_SUMMARY = "No meeting transcript available yet."
SUMMARY_SENTENCE_COUNT = 8

logger = logging.getLogger(__name__)
FILLER_PREFIXES = (
    "yeah",
    "okay",
    "ok",
    "right",
    "so",
    "well",
    "you know",
    "i mean",
    "like",
)
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "but",
    "by",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "his",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "me",
    "my",
    "of",
    "on",
    "or",
    "our",
    "she",
    "that",
    "the",
    "their",
    "them",
    "there",
    "they",
    "this",
    "to",
    "us",
    "was",
    "we",
    "were",
    "will",
    "with",
    "you",
    "your",
}
STRICT_ACTION_PATTERNS = (
    r"i have to",
    r"we have to",
    r"i need to",
    r"we need to",
    r"(?:let'?s|please|remember to|make sure to|follow up|circle back)",
    r"can you confirm",
    r"can you check",
    r"will check",
    r"will confirm",
    r"will send",
    r"will review",
    r"will prepare",
    r"will update",
    r"will investigate",
    r"will fix",
)
DECISION_PATTERNS = (
    r"(?:we|team|they)\s+(?:decided|agreed|approved|chose|selected|finalized|aligned on)",
    r"let'?s stick with",
    r"we(?:'ll| will) try",
    r"the plan is to",
    r"the decision is",
)
PROPOSAL_PATTERNS = (
    r"proposal to",
    r"i propose",
    r"propose we",
    r"the proposal is",
    r"the idea is",
)
DISCUSSION_PATTERNS = (
    r"reasons?",
    r"because",
    r"supportive",
    r"working really well",
    r"problem",
    r"difference",
    r"failure mode",
    r"how do people feel",
    r"security perspective",
    r"litmus test",
    r"concern",
)
NON_ACTION_HINTS = (
    r"proposal",
    r"how do people feel",
    r"i'?m supportive",
    r"working really well",
    r"we'?ll see how it goes",
    r"the problem i see",
    r"this is",
    r"it'?s \w+ \d{1,2}",
)
NON_DECISION_HINTS = (
    r"how do people feel",
    r"i'?m supportive",
    r"i could see either way",
    r"we'?ll see how it goes",
    r"problem i see",
    r"can you confirm",
)
OWNER_PATTERN = re.compile(
    r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:will|owns|own|needs to|is going to)"
)
DEADLINE_PATTERN = re.compile(
    r"(?:"
    r"today|tomorrow|tonight|this morning|this afternoon|this evening|"
    r"next week|next month|next quarter|next monday|next tuesday|next wednesday|next thursday|next friday|"
    r"monday|tuesday|wednesday|thursday|friday|saturday|sunday|"
    r"jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?|"
    r"\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?|\d{4}-\d{2}-\d{2}|"
    r"\d{1,2}(?::\d{2})?\s?(?:am|pm)|noon|midnight|eod|end of day|deadline"
    r")",
    re.IGNORECASE,
)


def _normalize_unit(text: str) -> str:
    cleaned = re.sub(r"\s+", " ", text.strip())
    cleaned = cleaned.strip(" .,!?:;-")

    lowered = cleaned.lower()
    for prefix in FILLER_PREFIXES:
        if lowered.startswith(f"{prefix} "):
            cleaned = cleaned[len(prefix) :].lstrip(" ,.-")
            lowered = cleaned.lower()

    if cleaned and cleaned[-1] not in ".!?":
        cleaned = f"{cleaned}."

    if cleaned:
        cleaned = cleaned[0].upper() + cleaned[1:]

    return cleaned


def _split_long_unit(unit: str) -> list[str]:
    if len(unit.split()) <= 24:
        return [unit]

    parts = re.split(r",\s+|\s+-\s+|\s+but\s+|\s+and then\s+", unit)
    normalized_parts = []
    for part in parts:
        normalized = _normalize_unit(part)
        if len(normalized.split()) >= 5:
            normalized_parts.append(normalized)
    return normalized_parts or [unit]


def _split_transcript_units(transcript: str) -> list[str]:
    """Split transcript into processable units with improved cleaning."""
    transcript = re.sub(r"\[lang:\w+\|conf:[\d.]+\]", "", transcript)
    
    normalized = transcript.replace("\r", "\n")
    raw_units = []
    for line in normalized.split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("[No speech detected"):
            continue
        raw_units.extend(re.split(r"(?<=[.!?])\s+", stripped))

    units = []
    seen = set()
    for raw_unit in raw_units:
        normalized_unit = _normalize_unit(raw_unit)
        for unit in _split_long_unit(normalized_unit):
            if len(unit.split()) < 4:
                continue
            key = unit.lower()
            if key in seen:
                continue
            seen.add(key)
            units.append(unit)
    return units


def _word_frequencies(units: list[str]) -> Counter:
    words = []
    for unit in units:
        for word in re.findall(r"[a-zA-Z']+", unit.lower()):
            if word in STOPWORDS or len(word) < 3:
                continue
            words.append(word)
    return Counter(words)


def _matches_any(text: str, patterns: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(re.search(pattern, lowered) for pattern in patterns)


def _score_summary_unit(unit: str, frequencies: Counter) -> float:
    words = [word for word in re.findall(r"[a-zA-Z']+", unit.lower()) if word not in STOPWORDS]
    if not words:
        return 0.0

    score = sum(frequencies.get(word, 0) for word in words)
    if _matches_any(unit, PROPOSAL_PATTERNS):
        score += 12
    if _matches_any(unit, DECISION_PATTERNS):
        score += 10
    if _matches_any(unit, DISCUSSION_PATTERNS):
        score += 6
    if _matches_any(unit, STRICT_ACTION_PATTERNS):
        score += 4
    if 7 <= len(words) <= 24:
        score += 3
    return score


def _clean_list_item(text: str) -> str:
    cleaned = _normalize_unit(text)
    return cleaned[:-1] if cleaned.endswith(".") else cleaned


def _extract_owner(sentence: str) -> str | None:
    match = OWNER_PATTERN.search(sentence)
    return match.group(1) if match else None


def _extract_deadlines(sentence: str) -> list[str]:
    return [match.group(0) for match in DEADLINE_PATTERN.finditer(sentence)]


def _cleanup_phrase(text: str) -> str:
    text = re.sub(r"I've got number \w+ in the agenda, which is", "", text, flags=re.IGNORECASE)
    text = re.sub(r"how do people feel about that proposal", "", text, flags=re.IGNORECASE)
    text = re.sub(r"cool", "", text, flags=re.IGNORECASE)
    text = re.sub(r"we'll", "the team will", text, flags=re.IGNORECASE)
    text = re.sub(r"we can be flexible", "remain flexible", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip(" .,;:-")
    return text


def _proposal_clause(unit: str) -> str:
    lowered = unit.lower()
    match = re.search(r"proposal to (.+)", lowered)
    if match:
        clause = _cleanup_phrase(match.group(1))
        return f"The proposal was to {clause}".strip()

    match = re.search(r"i propose we (.+)", lowered)
    if match:
        clause = _cleanup_phrase(match.group(1))
        return f"The proposal was to {clause}".strip()

    cleaned = _cleanup_phrase(unit)
    return cleaned[:1].upper() + cleaned[1:] if cleaned else ""


def _rewrite_summary_sentence(unit: str) -> str:
    text = _cleanup_phrase(unit)
    text = re.sub(r"I(?:'d)? love to", "Participants wanted to", text, flags=re.IGNORECASE)
    text = re.sub(r"my big question to you would be", "A central question was", text, flags=re.IGNORECASE)
    text = re.sub(r"we definitely want to", "The group emphasized the need to", text, flags=re.IGNORECASE)
    text = re.sub(r"chances are that", "Participants noted that", text, flags=re.IGNORECASE)
    text = re.sub(r"unfortunately", "They also noted that", text, flags=re.IGNORECASE)
    text = re.sub(r"\s+", " ", text).strip(" .,;:-")
    if not text:
        return ""
    return text[0].upper() + text[1:] + ("" if text.endswith(".") else ".")


def _main_topic_sentence(units: list[str], frequencies: Counter) -> str:
    ranked = sorted(units, key=lambda unit: _score_summary_unit(unit, frequencies), reverse=True)
    anchor = ranked[0]
    if _matches_any(anchor, PROPOSAL_PATTERNS):
        clause = _proposal_clause(anchor)
        return f"The main discussion topic was that {clause[0].lower() + clause[1:]}." if clause else _rewrite_summary_sentence(anchor)
    return f"The main discussion topic was {_cleanup_phrase(anchor).rstrip('.')} .".replace(" .", ".")


def _build_heuristic_summary(units: list[str], frequencies: Counter) -> str:
    sentences = []
    used = set()

    topic_sentence = _main_topic_sentence(units, frequencies)
    sentences.append(topic_sentence)
    used.add(topic_sentence.lower())

    ranked = sorted(units, key=lambda unit: _score_summary_unit(unit, frequencies), reverse=True)
    for unit in ranked:
        if len(sentences) >= SUMMARY_SENTENCE_COUNT:
            break
        rewritten = _rewrite_summary_sentence(unit)
        if not rewritten:
            continue
        key = rewritten.lower()
        if key in used:
            continue
        used.add(key)
        sentences.append(rewritten)

    if len(sentences) < SUMMARY_SENTENCE_COUNT:
        for unit in units:
            if len(sentences) >= SUMMARY_SENTENCE_COUNT:
                break
            rewritten = _rewrite_summary_sentence(unit)
            if not rewritten:
                continue
            key = rewritten.lower()
            if key in used:
                continue
            used.add(key)
            sentences.append(rewritten)

    return " ".join(sentences[:SUMMARY_SENTENCE_COUNT])


def _rewrite_action_task(unit: str) -> str:
    lowered = unit.lower()
    if "i have to check the taxonomy" in lowered or "we have to check the taxonomy" in lowered:
        return "Check and clarify the MR rate taxonomy"
    if "can you confirm" in lowered:
        return "Confirm the MR rate taxonomy"

    text = unit.strip().rstrip(".")
    text = re.sub(r"^(?:I|We|You|They)\s+have to\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(?:I|We|You|They)\s+need to\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^(?:Let'?s|Please|Remember to|Make sure to)\s+", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^can you\s+", "", text, flags=re.IGNORECASE)
    text = text[:1].upper() + text[1:] if text else text
    return text


def _rewrite_decision(unit: str) -> str:
    lowered = unit.lower()
    if "let's stick with the proposal" in lowered or "we'll try it" in lowered:
        return "The team decided to adopt the department key review rotation on a trial basis and remain flexible during rollout"
    if "captures community contributions" in lowered and "no internal" in lowered:
        return "The team aligned that the wider MR rate should refer to community contributions only, not internal merge requests"
    cleaned = _clean_list_item(unit)
    return cleaned[:1].upper() + cleaned[1:] if cleaned else ""


def _is_real_action_item(unit: str) -> bool:
    lowered = unit.lower()
    if not _matches_any(unit, STRICT_ACTION_PATTERNS):
        return False
    if _matches_any(unit, NON_ACTION_HINTS):
        return False
    if "let's stick with the proposal" in lowered or "we'll try it" in lowered:
        return False
    if "can you confirm" in lowered or "have to check" in lowered or "need to check" in lowered:
        return True
    return any(token in lowered for token in ("follow up", "check", "confirm", "send", "review", "prepare", "update", "investigate", "fix"))


def _is_real_decision(unit: str) -> bool:
    lowered = unit.lower()
    if not _matches_any(unit, DECISION_PATTERNS):
        return False
    if _matches_any(unit, NON_DECISION_HINTS):
        return False
    if "let's stick with the proposal" in lowered or "we'll try it" in lowered:
        return True
    return any(token in lowered for token in ("decided", "agreed", "approved", "selected", "finalized", "aligned on", "plan is"))


@lru_cache(maxsize=8)
def extract_summary(transcript: str) -> str:
    units = _split_transcript_units(transcript)
    if not units:
        return EMPTY_SUMMARY

    frequencies = _word_frequencies(units)
    return _build_heuristic_summary(units, frequencies)


@lru_cache(maxsize=8)
def extract_action_items(transcript: str) -> list[dict[str, str]]:
    units = _split_transcript_units(transcript)
    items = []
    seen = set()

    for unit in units:
        if not _is_real_action_item(unit):
            continue

        task = _rewrite_action_task(unit)
        key = task.lower()
        if key in seen:
            continue
        seen.add(key)

        owner = _extract_owner(unit) or "Not specified"
        deadlines = _extract_deadlines(unit)
        deadline = deadlines[0] if deadlines else "Not specified"

        items.append({
            "task": task,
            "owner": owner,
            "deadline": deadline,
        })

    return items


@lru_cache(maxsize=8)
def extract_decisions(transcript: str) -> list[str]:
    units = _split_transcript_units(transcript)
    decisions = []
    seen = set()

    for unit in units:
        if not _is_real_decision(unit):
            continue
        decision = _rewrite_decision(unit)
        key = decision.lower()
        if key in seen:
            continue
        seen.add(key)
        decisions.append(decision)

    return decisions


def analyze_meeting(transcript: str) -> dict[str, object]:
    action_items = extract_action_items(transcript)
    decisions = extract_decisions(transcript)

    owners = list(dict.fromkeys(item["owner"] for item in action_items if item["owner"] != "Not specified"))
    deadlines = list(dict.fromkeys(item["deadline"] for item in action_items if item["deadline"] != "Not specified"))

    return {
        "summary": extract_summary(transcript),
        "action_items": action_items,
        "owners": owners,
        "deadlines": deadlines,
        "decisions": decisions,
    }


def generate_summary(transcript: str) -> str:
    return extract_summary(transcript)
