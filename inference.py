import os
import json
import requests

try:
    from openai import OpenAI
except Exception:
    OpenAI = None

# =========================
# CONFIG (STRICT)
# =========================

ENV_URL = os.getenv("ENV_URL", "https://sharvandeep-ticket-routing-openenv.hf.space")

# Required runtime configuration
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "openai/gpt-4o-mini")
HF_TOKEN = os.getenv("HF_TOKEN")

client = OpenAI(base_url=API_BASE_URL, api_key=HF_TOKEN) if (OpenAI and HF_TOKEN) else None

# =========================
# NORMALIZATION
# =========================

def normalize_action(action):
    return {
        "department": str(action.get("department", "general")).lower()
        if action.get("department", "").lower() in ["billing", "technical", "account", "general"]
        else "general",

        "priority": str(action.get("priority", "low")).lower()
        if action.get("priority", "").lower() in ["low", "medium", "high"]
        else "low",

        "escalation": str(action.get("escalation", "no")).lower()
        if action.get("escalation", "").lower() in ["yes", "no"]
        else "no",
    }

# =========================
# LLM AGENT
# =========================

def get_action(ticket_text):
    prompt = f"""
Classify this support ticket STRICTLY using:

department: billing | technical | account | general  
priority: low | medium | high  
escalation: yes | no  

Return ONLY JSON.

Ticket: {ticket_text}
"""

    if client is not None:
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )

            content = response.choices[0].message.content.strip()

            start = content.find("{")
            end = content.rfind("}") + 1

            if start != -1 and end != -1:
                return json.loads(content[start:end])

        except Exception:
            # Fall back to deterministic rules when LLM call fails.
            pass

    # fallback
    text = ticket_text.lower()

    if "charged" in text:
        return {"department": "billing", "priority": "high", "escalation": "yes"}
    elif "password" in text:
        return {"department": "technical", "priority": "high", "escalation": "yes"}
    elif "email" in text or "username" in text:
        return {"department": "account", "priority": "low", "escalation": "no"}
    elif "buffering" in text:
        return {"department": "technical", "priority": "medium", "escalation": "no"}
    return {"department": "general", "priority": "low", "escalation": "no"}

# =========================
# RUN
# =========================

def run():
    total_reward = 0
    steps = 0
    task_name = "unknown"

    # RESET
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

    # START
    print(f"[START] task={task_name} env=ticket_routing_openenv model={MODEL_NAME}", flush=True)

    done = False

    while not done:
        try:
            ticket_text = data.get("ticket_text")

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

        reward = result.get("reward", 0)
        total_reward += reward
        steps += 1

        print(f"[STEP] step={steps} action={repr(action)} reward={reward} done={done} error=None", flush=True)

        done = result.get("done", True)
        data = result.get("observation", {})

    raw_score = total_reward / steps if steps > 0 else 0.0
    score = 0.05 + (raw_score * 0.90)

    success = score > 0.5
    print(f"[END] success={success} steps={steps} score={score} rewards={total_reward}", flush=True)

# ENTRY
if __name__ == "__main__":
    run()