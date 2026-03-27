def grade(action, correct):
    score = 0.0

    if action["department"] == correct["department"]:
        score += 0.4

    if action["priority"] == correct["priority"]:
        score += 0.3

    if action["escalation"] == correct["escalation"]:
        score += 0.3

    return score