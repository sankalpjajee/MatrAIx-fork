"""Clinical-trial pre-screening chatbot sidecar (rule-based smoke implementation).

A deterministic screener for the `chat_prescreening-*` tasks: it loads a
trial protocol (criteria, probe questions, applicability rules) from
./protocols/, walks the participant through every applicable criterion one
question at a time, and ends with the fenced-JSON final assessment the task
verifiers check. Answers it cannot read as yes / no / not-sure trigger one
explicit confirmation question, so any cooperative participant can complete
the screen.

Protocol selection, in order: request body `protocolId` (or `title`) matching
a file in ./protocols/ or a `protocol_id` inside one; env
`PRESCREENING_PROTOCOL_ID`; the first protocol alphabetically.

This is a smoke-run product (same tier as the Acme support sidecar). A
production LLM screener can replace it by pointing the tasks'
`CHATBOT_UPSTREAM_PRESCREENING` at a different endpoint.
"""

from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path

from flask import Flask, jsonify, request

app = Flask(__name__)

PROTOCOLS_DIR = Path(__file__).resolve().parent / "protocols"

UNKNOWN_RE = re.compile(
    r"\b(don'?t know|do not know|not sure|unsure|no idea|can'?t remember|"
    r"cannot remember|not certain|never (checked|measured|tested)|"
    r"i'?d have to check|would have to check)\b",
    re.IGNORECASE,
)
NO_RE = re.compile(
    r"^\s*(no|nope|nah|none)\b|\b(never|don'?t have|do not have|haven'?t|"
    r"has not|hasn'?t|not applicable|doesn'?t apply|not pregnant|"
    r"nothing like that|not that i know|no,)\b",
    re.IGNORECASE,
)
YES_RE = re.compile(
    r"^\s*(yes|yeah|yep|yup|correct|definitely|absolutely|sure)\b|"
    r"\b(i do\b(?!n'?t| not)|that'?s right|yes,)\b",
    re.IGNORECASE,
)

NUMBER_RE = re.compile(r"\d+(?:\.\d+)?")

# Criteria whose probe polarity is inverted (negatively phrased, e.g. "NO prior
# diagnosis of...") or whose probe is compound ("...and if so, are you...").
# A raw yes/no to their probe is semantically ambiguous, so those criteria are
# always resolved through the confirmation question, which restates the
# criterion in satisfaction terms.
NEGATED_CRITERION_RE = re.compile(
    r"\b(no prior|no history|no known|no current|not currently|has not|"
    r"have not|does not|is not)\b",
    re.IGNORECASE,
)


def _needs_confirmation(criterion) -> bool:
    return bool(NEGATED_CRITERION_RE.search(criterion["text"])) or \
        ", and if so" in criterion.get("probe", "").lower()

_BOUND_PATTERNS = [
    (r"between\s+(\d+(?:\.\d+)?)\s*%?\s*(?:and|to|[-\u2013])\s*(\d+(?:\.\d+)?)",
     lambda m: (float(m.group(1)), float(m.group(2)), True, True)),
    (r"(\d+(?:\.\d+)?)\s*(?:%|years?|hours?|days?|months?)?\s*(?:to|[-\u2013])\s*"
     r"(\d+(?:\.\d+)?)",
     lambda m: (float(m.group(1)), float(m.group(2)), True, True)),
    (r"(?:at least|minimum of|no fewer than)\s+(\d+(?:\.\d+)?)|"
     r"(\d+(?:\.\d+)?)[^.]{0,24}?\bor more\b",
     lambda m: (float(m.group(1) or m.group(2)), float("inf"), True, True)),
    (r"(?:less than|under|fewer than|below)\s+(\d+(?:\.\d+)?)",
     lambda m: (float("-inf"), float(m.group(1)), True, False)),
    (r"(?:at most|no more than|up to)\s+(\d+(?:\.\d+)?)",
     lambda m: (float("-inf"), float(m.group(1)), True, True)),
    (r"(?:more than|over|above)\s+(\d+(?:\.\d+)?)",
     lambda m: (float(m.group(1)), float("inf"), False, True)),
    (r"(?:within|in) the (?:past|last)\s+(\d+(?:\.\d+)?)",
     lambda m: (0.0, float(m.group(1)), True, True)),
]


def _criterion_bounds(text):
    """(lo, hi, lo_inclusive, hi_inclusive) when the criterion states exactly one
    numeric condition; None when zero or several (multi-constraint criteria fall
    back to the yes/no confirmation flow)."""
    lowered = text.lower()
    found = []
    for pattern, build in _BOUND_PATTERNS:
        match = re.search(pattern, lowered)
        if match:
            found.append(build(match))
            lowered = lowered.replace(match.group(0), " ", 1)
            if any(re.search(p, lowered) for p, _ in _BOUND_PATTERNS):
                return None  # more than one numeric condition -> ambiguous
            break
    return found[0] if found else None


def _numeric_answer(criterion, message):
    """Compare a single number in the reply against the criterion's stated
    bounds. Returns 'yes' (condition satisfied) / 'no', or None when not
    applicable (no bounds, or not exactly one number in the reply)."""
    bounds = _criterion_bounds(criterion["text"])
    if bounds is None:
        return None
    numbers = NUMBER_RE.findall(message)
    if len(numbers) != 1:
        return None
    value = float(numbers[0])
    lo, hi, lo_inc, hi_inc = bounds
    ok_lo = value >= lo if lo_inc else value > lo
    ok_hi = value <= hi if hi_inc else value < hi
    return "yes" if (ok_lo and ok_hi) else "no"
FEMALE_RE = re.compile(r"\b(female|woman|girl|f)\b", re.IGNORECASE)
MALE_RE = re.compile(r"\b(male|man|boy|m)\b", re.IGNORECASE)

_sessions: dict[str, dict] = {}


def _load_protocols() -> dict[str, dict]:
    protocols = {}
    for path in sorted(PROTOCOLS_DIR.glob("*.json")):
        protocol = json.loads(path.read_text(encoding="utf-8"))
        protocols[path.stem] = protocol
        protocols.setdefault(protocol.get("protocol_id", path.stem), protocol)
    return protocols


PROTOCOLS = _load_protocols()


def _pick_protocol(payload: dict) -> dict:
    for key in ("protocolId", "title"):
        wanted = str(payload.get(key) or "").strip()
        if wanted and wanted in PROTOCOLS:
            return PROTOCOLS[wanted]
    env_id = os.environ.get("PRESCREENING_PROTOCOL_ID", "").strip()
    if env_id and env_id in PROTOCOLS:
        return PROTOCOLS[env_id]
    return PROTOCOLS[sorted(k for k in PROTOCOLS if k.startswith("chat_"))[0]]


def _uses_sex(protocol: dict) -> bool:
    return any("sex" in (c.get("not_applicable_when") or {}) for c in protocol["criteria"])


def _applicable(criterion: dict, sex: str | None) -> bool:
    condition = criterion.get("not_applicable_when") or {}
    if not condition:
        return True
    return not all(
        (key == "sex" and sex is not None and sex == value) or False
        for key, value in condition.items()
    )


def _parse_yes_no_unknown(text: str) -> str | None:
    if UNKNOWN_RE.search(text):
        return "unknown"
    if NO_RE.search(text):
        return "no"
    if YES_RE.search(text):
        return "yes"
    return None


def _greeting(protocol: dict) -> str:
    return (
        f"Hello! I can help you find out whether you might qualify for the study "
        f"\"{protocol['study_title']}\" ({protocol['protocol_id']}). I'll go through "
        "the eligibility questions one at a time. Please note this is a preliminary "
        "pre-screening only - it does not guarantee enrollment, and the study team "
        "will confirm final eligibility against your records."
    )


def _confirm_question(criterion: dict) -> str:
    if criterion["kind"] == "inclusion":
        return (
            f"Thanks. For this study, the requirement is: \"{criterion['text']}\" "
            "Based on what you just told me, do you meet this requirement - "
            "yes, no, or not sure?"
        )
    return (
        f"Thanks. This study excludes people for whom the following applies: "
        f"\"{criterion['text']}\" Does this apply to you - yes, no, or not sure?"
    )


def _record(state: dict, criterion: dict, answer: str) -> None:
    if answer == "unknown":
        status = "unknown"
    elif criterion["kind"] == "inclusion":
        status = "ok" if answer == "yes" else "fail"
    else:
        status = "fail" if answer == "yes" else "ok"
    state["results"][criterion["id"]] = status


def _next_prompt(state: dict) -> str:
    criteria = state["criteria"]
    index = state["index"]
    if index < len(criteria):
        return criteria[index]["probe"]
    return _final_assessment(state)


def _final_assessment(state: dict) -> str:
    results = state["results"]
    not_met = [cid for cid, status in results.items() if status == "fail"]
    unknown = [cid for cid, status in results.items() if status == "unknown"]
    if not_met:
        eligibility = "likely_ineligible"
        summary = (
            "Based on your answers, you are likely NOT eligible for this study "
            f"(criteria not met: {', '.join(not_met)})."
        )
    elif unknown:
        eligibility = "insufficient_information"
        summary = (
            "I could not determine some requirements from your answers "
            f"({', '.join(unknown)}), so there is not enough information for a "
            "preliminary result yet."
        )
    else:
        eligibility = "likely_eligible"
        summary = "Based on your answers, you appear likely eligible for this study."
    verdict = {
        "final_assessment": True,
        "eligibility": eligibility,
        "criteria_not_met": not_met,
        "criteria_unknown": unknown,
        "notes": "Deterministic pre-screen from self-reported answers.",
    }
    return (
        f"That was my last question. {summary} Remember, this is a preliminary "
        "pre-screen only - the study team makes the final eligibility decision.\n\n"
        "```json\n" + json.dumps(verdict, indent=1) + "\n```"
    )


def _advance(state: dict, message: str) -> str:
    # Optional one-time sex question so sex-conditional criteria can be skipped.
    if state["stage"] == "sex":
        if FEMALE_RE.search(message):
            state["sex"] = "female"
        elif MALE_RE.search(message):
            state["sex"] = "male"
        state["criteria"] = [
            c for c in state["protocol"]["criteria"] if _applicable(c, state["sex"])
        ]
        state["stage"] = "criteria"
        return _next_prompt(state)

    criteria = state["criteria"]
    if state["index"] >= len(criteria):
        return (
            "The screening is complete - my preliminary assessment is above. "
            "The study team will confirm final eligibility."
        )

    criterion = criteria[state["index"]]
    answer = _parse_yes_no_unknown(message)
    if not state["confirming"] and answer != "unknown" and _needs_confirmation(criterion):
        state["confirming"] = True
        return _confirm_question(criterion)
    if answer is None and not state["confirming"]:
        answer = _numeric_answer(criterion, message)

    if answer is None and not state["confirming"]:
        state["confirming"] = True
        return _confirm_question(criterion)

    if answer is None:
        answer = "unknown"  # unreadable twice -> per protocol, treat as unknown

    _record(state, criterion, answer)
    state["confirming"] = False
    state["index"] += 1
    return _next_prompt(state)


@app.get("/health")
def health():
    return jsonify({"status": "ok", "protocols": sorted(PROTOCOLS)})


@app.post("/v1/messages")
def post_message():
    payload = request.get_json(silent=True) or {}
    message = str(payload.get("message", "")).strip()
    if not message:
        return jsonify({"error": "message must not be empty"}), 400

    session_id = str(payload.get("sessionId") or "").strip() or uuid.uuid4().hex
    state = _sessions.get(session_id)
    if state is None:
        protocol = _pick_protocol(payload)
        state = {
            "protocol": protocol,
            "criteria": list(protocol["criteria"]),
            "index": 0,
            "results": {},
            "confirming": False,
            "sex": None,
            "stage": "sex" if _uses_sex(protocol) else "criteria",
            "turn": 0,
            "messages": [],
        }
        _sessions[session_id] = state
        if state["stage"] == "sex":
            first_question = (
                "First, may I ask your sex? Some questions only apply to certain "
                "participants."
            )
        else:
            first_question = _next_prompt(state)
        reply = f"{_greeting(protocol)}\n\n{first_question}"
    else:
        reply = _advance(state, message)

    state["turn"] += 1
    state["messages"].append({"role": "user", "content": message})
    state["messages"].append({"role": "assistant", "content": reply})
    turn_view = {
        "index": state["turn"],
        "userMessage": message,
        "assistantReply": reply,
    }
    return jsonify({"sessionId": session_id, "reply": reply, "turn": turn_view})


@app.get("/v1/conversation")
def get_conversation():
    session_id = str(request.args.get("sessionId") or "").strip()
    state = _sessions.get(session_id)
    if state is None:
        return jsonify({"sessionId": session_id, "messages": []})
    return jsonify({
        "sessionId": session_id,
        "domain": "clinical_trial_prescreening",
        "messages": state["messages"],
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
