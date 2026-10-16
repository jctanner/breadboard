"""Mechanical assessment-content contract, independent of model/content judging.

Recognize a completed role judgment, recommendation and explanatory content in
the assigned strategy's section. This is a format/content check, not a claim
that the explanation is accurate or that the whole report stayed in scope.
"""
import re

CONTRACT = "role-assessment-v1"
TARGET_HEADING = re.compile(r"^#{1,6}\s+((?:RHAISTRAT|STRAT)-\d+):[^\n]*", re.M)
FIELDS = {
    "feasibility": ("Feasibility", r"feasible|infeasible|needs revision"),
    "testability": ("Testability", r"(?:(?:partially|largely|mostly|fully) )?testable|untestable"),
    "scope": ("Scope assessment", r"right[- ]sized|too large|too small|unbounded"),
    "architecture": ("Architecture assessment", r"(?:(?:mostly|largely) )?sound|concerns identified|conflicts with platform"),
}
SUPPORT = {
    "feasibility": ("Effort estimate", "RFE alignment", "Key concerns"),
    "testability": ("Missing edge cases", "Untestable criteria", "Test complexity"),
    "scope": ("Effort vs scope", "RFE coverage", "Scope risks"),
    "architecture": ("Missing dependencies", "Incorrect assumptions", "Cross-component risks", "Grounding"),
}
FIELD = re.compile(r"^\s*(?:\*\*)?([A-Za-z][A-Za-z /-]*?)(?:\*\*)?"
                   r"(?:\s*\([^\n)]*\))?\s*:(?:\*\*)?\s*([^\n]*)", re.M)
PLACEHOLDER = re.compile(r"^\s*(?:<[^>\n]+>|(?:TODO|TBD|placeholder|lorem ipsum)\b)", re.I)
FINDINGS = re.compile(r"^(?:\*\*(?:Detailed findings|Findings|Rationale)\*\*|"
                      r"#{1,6}\s+(?:Detailed findings|Findings|Rationale))\s*:?\s*$", re.M | re.I)
NUMBERED_FINDINGS = re.compile(r"^\s*\d+[.)]\s+(.+)$", re.M)
STATUS = re.compile(
    r"^(?:skill execution completed|review_scope_error:|(?:api |connection |upstream )?error\b|"
    r"(?:i(?:'ve| have) |we(?:'ve| have) )?(?:launched|started)\b|"
    r"(?:i(?:'ll| will| am)|we(?:'ll| will| are))\b|"
    r"(?:review|assessment|analysis)(?: is)? (?:pending|in progress|not yet|not completed)\b|"
    r"(?:pending|waiting|awaiting|working on|unable to|failed to)\b)", re.I)


def _explains(value):
    """Exclude scaffolding/status; require an explanatory clause, not padding.

    Six words is a transparent minimum for a clause, not a quality score or a
    whole-report length threshold. None-found reports can pass with a rationale.
    """
    for line in value.splitlines():
        line = re.sub(r"^\s*(?:[-*]|\d+[.)])\s+", "", line).strip()
        if not line or line.startswith(("#", "|", "```", ">")) or FIELD.match(line):
            continue
        if PLACEHOLDER.search(line) or STATUS.match(line):
            continue
        if len(re.findall(r"[A-Za-z0-9]+(?:[-'][A-Za-z0-9]+)*", line)) >= 6:
            return True
    return False


def classify(report, key, role, *, is_error=False):
    headings = list(TARGET_HEADING.finditer(report))
    targets = [match[1] for match in headings]
    result = {"contract": CONTRACT, "classification": "incomplete", "assessment_present": False,
              "target_identified": key in targets, "reported_targets": targets,
              "exclusive_report_target": targets == [key]}

    def finish(classification, reason):
        return result | {"classification": classification, "reason": reason,
                         "assessment_present": classification == "assessment"}

    if is_error:
        return finish("error", "tool result marked is_error")
    if not report.strip():
        return finish("missing", "no assessment text")
    if report.strip() == "Skill execution completed":
        return finish("acknowledgement", "completion marker without an assessment")
    if STATUS.match(report.lstrip()):
        return finish("status_or_error", "status/error text instead of a completed assessment")
    matches = [index for index, heading in enumerate(headings) if heading[1] == key]
    if len(matches) != 1:
        return finish("incomplete", "expected one identifiable section for the assigned strategy")
    index = matches[0]
    section = report[headings[index].end():headings[index + 1].start() if index + 1 < len(headings) else len(report)]
    fields = list(FIELD.finditer(section))
    values = {}
    for i, field in enumerate(fields):
        # Keep list/paragraph explanations attached to their field.
        values.setdefault(field[1].lower(), []).append(
            section[field.start(2):fields[i + 1].start() if i + 1 < len(fields) else len(section)].strip())
    recommendations = values.get("recommendation", [])
    if not recommendations:
        return finish("incomplete", "missing or ambiguous completed recommendation")
    decisions = set()
    for value in recommendations:
        recommendation = re.match(r"(approve|revise|reject|skipped)\b", value, re.I)
        if not recommendation or PLACEHOLDER.search(value) or re.match(
                r"\s*(?:/|or\b)\s*(?:approve|revise|reject|skipped)\b",
                value[recommendation.end():], re.I):
            return finish("incomplete", "recommendation is not a completed decision")
        decisions.add(recommendation[1].lower())
    if len(decisions) != 1:
        return finish("incomplete", "missing or ambiguous completed recommendation")
    result["recommendation"] = next(iter(decisions))
    label, outcomes = FIELDS[role]
    judgments = values.get(label.lower(), [])
    if result["recommendation"] == "skipped":
        if role == "architecture" and len(judgments) == 1 and re.match(
                r"no architecture context available\b", judgments[0], re.I):
            return finish("skipped", "architecture context unavailable; no assessment claimed")
        return finish("incomplete", "unsupported role skip")
    if not judgments:
        return finish("incomplete", "missing or unfinished assigned-role judgment")
    normalized = set()
    for value in judgments:
        judgment = re.match(r"(?:" + outcomes + r")\b", value, re.I)
        if (not judgment or PLACEHOLDER.search(value) or re.match(
                r"\s*(?:/|or\b)\s*(?:" + outcomes + r")\b", value[judgment.end():], re.I)):
            return finish("incomplete", "missing or unfinished assigned-role judgment")
        normalized.add(judgment[0].lower().replace("-", " "))
    if len(normalized) != 1:
        return finish("incomplete", "conflicting assigned-role judgments")
    explanations = [judgments[0], *(value for name in SUPPORT[role]
                                   for value in values.get(name.lower(), []))]
    explanations.extend(section[heading.end():] for heading in FINDINGS.finditer(section))
    explanations.extend(heading[1] for heading in NUMBERED_FINDINGS.finditer(section))
    if not any(_explains(value) for value in explanations):
        return finish("incomplete", "no explanatory role content beyond verdict/status/boilerplate")
    return finish("assessment", "assigned-role judgment, recommendation and explanation present")
