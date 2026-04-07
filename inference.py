import os
import json
import requests

# Try importing OpenAI safely
try:
    from openai import OpenAI
except:
    OpenAI = None

# =========================
# CONFIG
# =========================

ENV_URL = "https://sharvandeep-ticket-routing-openenv.hf.space"

API_BASE_URL = os.getenv("API_BASE_URL")
MODEL_NAME = os.getenv("MODEL_NAME")
HF_TOKEN = os.getenv("HF_TOKEN")

# Safe client init
client = None
if OpenAI and API_BASE_URL and MODEL_NAME and HF_TOKEN:
    try:
        client = OpenAI(
            base_url=API_BASE_URL,
            api_key=HF_TOKEN
        )
    except Exception as e:
        print("Client init failed:", e, flush=True)
        client = None

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

    # Try LLM
    if client:
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0
            )

            content = response.choices[0].message.content.strip()

            start = content.find("{")
            end = content.rfind("}") + 1

            if start != -1 and end != -1:
                try:
                    return json.loads(content[start:end])
                except:
                    pass

        except Exception as e:
            print("LLM error:", e, flush=True)

    # Rule fallback
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
# RUN EPISODE (VALIDATOR SAFE)
# =========================

def run():
    total_reward = 0
    steps = 0
    task_name = "unknown"

    try:
        response = requests.post(f"{ENV_URL}/reset", timeout=10)
        data = response.json()
    except Exception as e:
        print("Reset failed:", e, flush=True)
        return

    if not isinstance(data, dict) or "ticket_text" not in data:
        print("Invalid reset response:", data, flush=True)
        return

    task_name = data.get("task_type", "unknown")

    # ✅ START BLOCK
    print(f"[START] task={task_name}", flush=True)

    done = False

    while not done:
        try:
            ticket_text = data.get("ticket_text")

            if not ticket_text:
                print("Missing ticket_text:", data, flush=True)
                break

            raw_action = get_action(ticket_text)
            action = normalize_action(raw_action)

            step_response = requests.post(
                f"{ENV_URL}/step",
                json=action,
                timeout=10
            )

            result = step_response.json()

        except Exception as e:
            print("Step failed:", e, flush=True)
            break

        if not isinstance(result, dict) or "reward" not in result:
            print("Invalid step response:", result, flush=True)
            break

        reward = result.get("reward", 0)
        total_reward += reward
        steps += 1

        # ✅ STEP BLOCK
        print(f"[STEP] step={steps} reward={reward}", flush=True)

        done = result.get("done", True)
        data = result.get("observation", {})

    score = total_reward / steps if steps > 0 else 0

    # ✅ END BLOCK
    print(f"[END] task={task_name} score={score} steps={steps}", flush=True)

# =========================
# ENTRY POINT
# =========================

if __name__ == "__main__":
    run()