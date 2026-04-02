import requests
import os
import json
from openai import OpenAI

# =========================
# CONFIG
# =========================

ENV_URL = "https://sharvandeep-ticket-routing-openenv.hf.space"

API_BASE_URL = os.getenv("API_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
HF_TOKEN = os.getenv("HF_TOKEN")

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN
)

# =========================
# NORMALIZATION
# =========================

def normalize_action(action):
    dept_map = {
        "billing": "billing",
        "technical support": "technical",
        "technical": "technical",
        "account": "account",
        "user accounts": "account",
        "customer support": "account",
        "customer service": "account",
        "general": "general"
    }

    priority_map = {
        "low": "low",
        "medium": "medium",
        "high": "high"
    }

    escalation_map = {
        "yes": "yes",
        "no": "no",
        "immediate": "yes"
    }

    return {
        "department": dept_map.get(action.get("department", "").lower(), "general"),
        "priority": priority_map.get(action.get("priority", "").lower(), "low"),
        "escalation": escalation_map.get(action.get("escalation", "").lower(), "no")
    }

# =========================
# LLM AGENT
# =========================

def get_action(ticket_text):
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{
                "role": "user",
                "content": f"""
Classify this ticket STRICTLY using only these values:
Use ONLY these exact values. No variations. Lowercase only.
department: billing | technical | account | general
priority: low | medium | high
escalation: yes | no

Return ONLY JSON.

Ticket: {ticket_text}
"""
            }],
            temperature=0
        )

        content = response.choices[0].message.content.strip()

        start = content.find("{")
        end = content.rfind("}") + 1

        if start != -1 and end != -1:
            return json.loads(content[start:end])

    except:
        pass

    # 🔥 STRONG RULE-BASED (backup)
    text = ticket_text.lower()

    if "charged" in text:
        return {"department": "billing", "priority": "high", "escalation": "yes"}

    elif "password" in text or "login" in text:
        return {"department": "technical", "priority": "high", "escalation": "yes"}

    elif "username" in text or "email" in text or "account" in text:
        return {"department": "account", "priority": "low", "escalation": "no"}

    elif "buffering" in text or "slow" in text or "loading" in text:
        return {"department": "technical", "priority": "medium", "escalation": "no"}

    elif "refund" in text or "payment" in text:
        return {"department": "billing", "priority": "medium", "escalation": "yes"}

    else:
        return {"department": "general", "priority": "low", "escalation": "no"}
# =========================
# RUN EPISODE
# =========================

def run():
    total_reward = 0
    steps = 0

    # Start environment
    response = requests.post(f"{ENV_URL}/reset")
    data = response.json()

    if not data or "ticket_text" not in data:
        print("Invalid response from environment")
        return

    done = False

    while not done:
        ticket_text = data["ticket_text"]

        raw_action = get_action(ticket_text)
        action = normalize_action(raw_action)

        step_response = requests.post(f"{ENV_URL}/step", json=action)
        result = step_response.json()

        reward = result["reward"]
        total_reward += reward
        steps += 1

        print(f"[STEP] {steps}")
        print(f"Ticket: {ticket_text}")
        print(f"Action: {action}")
        print(f"Reward: {reward}")
        print("-" * 40)

        done = result["done"]
        data = result["observation"]

    print(f"\n[END] Final Score: {total_reward / steps}")

# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    run()