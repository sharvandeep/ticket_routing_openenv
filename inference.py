import requests

BASE_URL = "https://sharvandeep-ticket-routing-openenv.hf.space"

def get_action(ticket_text):
    """
    Simple rule-based agent (baseline)
    """
    text = ticket_text.lower()

    if "charged" in text:
        return {"department": "billing", "priority": "high", "escalation": "yes"}
    elif "password" in text or "login" in text:
        return {"department": "technical", "priority": "high", "escalation": "yes"}
    elif "username" in text or "email" in text:
        return {"department": "account", "priority": "low", "escalation": "no"}
    elif "buffering" in text:
        return {"department": "technical", "priority": "medium", "escalation": "no"}
    else:
        return {"department": "general", "priority": "low", "escalation": "no"}


def run():
    total_reward = 0
    steps = 0

    # Start environment
    response = requests.get(f"{BASE_URL}/reset")
    data = response.json()

    done = False

    while not done:
        ticket_text = data["ticket_text"]

        action = get_action(ticket_text)

        step_response = requests.post(f"{BASE_URL}/step", json=action)
        result = step_response.json()

        reward = result["reward"]
        total_reward += reward
        steps += 1

        print(f"Step {steps}")
        print(f"Ticket: {ticket_text}")
        print(f"Action: {action}")
        print(f"Reward: {reward}")
        print("-" * 40)

        done = result["done"]
        data = result["observation"]

    print(f"\nFinal Score: {total_reward / steps}")


if __name__ == "__main__":
    run()