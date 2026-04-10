EPSILON = 0.0001


def _strict_unit_interval(value: float) -> float:
    """Clamp score into the strict open interval (0, 1)."""
    if value <= 0.0:
        return EPSILON
    if value >= 1.0:
        return 1.0 - EPSILON
    return value


def grade(action, correct):
    """
    Returns a deterministic score in (0.0, 1.0).
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

    return round(_strict_unit_interval(score), 4)