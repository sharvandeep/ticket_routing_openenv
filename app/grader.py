def grade(action, correct):
    # Keep scores strictly within (0, 1) for evaluator compatibility.
    score = 0.0

    if action.get("department") == correct.get("department"):
        score += 0.4

    if action.get("priority") == correct.get("priority"):
        score += 0.3

    if action.get("escalation") == correct.get("escalation"):
        score += 0.3

    # Map [0.0, 1.0] -> [0.05, 0.95] to avoid exact boundary values.
    bounded_score = 0.05 + (score * 0.90)
    return round(bounded_score, 4)