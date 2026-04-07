import os
import json
from openai import OpenAI
import requests

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
        "technical": "technical",
        "technical support": "technical",
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
# LLM + RULE HYBRID AGENT
# =========================

def get_action(ticket_text):
    prompt = f"""
You are a STRICT customer support classifier.

ONLY use these exact values (lowercase only):

department: billing | technical | account | general  
priority: low | medium | high  
escalation: yes | no  

Return ONLY JSON:
{{
  "department": "...",
  "priority": "...",
  "escalation": "..."
}}

Ticket: {ticket_text}
"""

    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )

        content = response.choices[0].message.content.strip()

        # Extract JSON safely
        start = content.find("{")
        end = content.rfind("}") + 1

        if start != -1 and end != -1:
            action = json.loads(content[start:end])

            # =========================
            # SMART CORRECTION LAYER
            # =========================

            text = ticket_text.lower()

            if "charged" in text or "payment" in text or "refund" in text:
                action["department"] = "billing"
                action["priority"] = "high"
                action["escalation"] = "yes"

            elif "password" in text or "login" in text:
                action["department"] = "technical"
                action["priority"] = "high"
                action["escalation"] = "yes"

            elif "username" in text or "email" in text or "account" in text:
                action["department"] = "account"
                action["priority"] = "low"
                action["escalation"] = "no"

            elif "buffering" in text or "slow" in text or "loading" in text:
                action["department"] = "technical"
                action["priority"] = "medium"
                action["escalation"] = "no"

            return action

    except Exception as e:
        print("LLM error:", e)

    # =========================
    # RULE-BASED FALLBACK
    # =========================

    text = ticket_text.lower()

    if "charged" in text or "payment" in text or "refund" in text:
        return {"department": "billing", "priority": "high", "escalation": "yes"}

    elif "password" in text or "login" in text:
        return {"department": "technical", "priority": "high", "escalation": "yes"}

    elif "username" in text or "email" in text or "account" in text:
        return {"department": "account", "priority": "low", "escalation": "no"}

    elif "buffering" in text or "slow" in text or "loading" in text:
        return {"department": "technical", "priority": "medium", "escalation": "no"}

    else:
        return {"department": "general", "priority": "low", "escalation": "no"}
# =========================
# RUN EPISODE (SAFE VERSION)
# =========================
def run():
    total_reward = 0
    steps = 0

    try:
        response = requests.post(f"{ENV_URL}/reset")
        data = response.json()
    except Exception as e:
        print("Reset failed:", e)
        return

    # ✅ SAFE CHECK
    if not isinstance(data, dict) or "ticket_text" not in data:
        print("Invalid reset response:", data)
        return

    done = False

    while not done:
        try:
            # ✅ SAFE ACCESS
            ticket_text = data.get("ticket_text")

            if not ticket_text:
                print("Missing ticket_text:", data)
                break

            raw_action = get_action(ticket_text)
            action = normalize_action(raw_action)

            step_response = requests.post(f"{ENV_URL}/step", json=action)
            result = step_response.json()

        except Exception as e:
            print("Step failed:", e)
            break

        # ✅ SAFE CHECK AGAIN
        if not isinstance(result, dict) or "reward" not in result:
            print("Invalid step response:", result)
            break

        reward = result.get("reward", 0)
        total_reward += reward
        steps += 1

        print(f"[STEP] {steps}")
        print(f"Ticket: {ticket_text}")
        print(f"Action: {action}")
        print(f"Reward: {reward}")
        print("-" * 40)

        done = result.get("done", True)
        data = result.get("observation", {})

    if steps > 0:
        print(f"\n[END] Final Score: {total_reward / steps}")
    else:
        print("\n[END] No steps executed")

# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    run()