def grade(action, correct):
    """
    Returns a deterministic score in [0.0, 1.0].
    +0.4 for department
    +0.3 for priority
    +0.3 for escalation
    """
    score = 0.0

    if action.get("department") == correct.get("department"):
        score += 0.4

    if action.get("priority") == correct.get("priority"):
        score += 0.3

    if action.get("escalation") == correct.get("escalation"):
        score += 0.3

    return round(min(max(score, 0.0), 1.0), 4)