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

def fetch_tasks():
    urls = [f"{ENV_URL}/tasks?format=object", f"{ENV_URL}/tasks"]

    for url in urls:
        try:
            response = requests.get(url, timeout=10)
            payload = response.json()

            if isinstance(payload, dict) and isinstance(payload.get("tasks"), list):
                return payload["tasks"]
            if isinstance(payload, list):
                return payload
        except Exception:
            pass

    return []


def has_grader(task):
    return bool(
        task.get("graders")
        or task.get("grader")
        or task.get("grader_id")
        or task.get("grader_ids")
    )


def run_single_task(task):
    task_id = task.get("id", "unknown")

    try:
        response = requests.post(f"{ENV_URL}/reset", json={"task_id": task_id}, timeout=10)
        data = response.json()
    except Exception as e:
        print(f"[START] task={task_id} env=ticket_routing_openenv model={MODEL_NAME}", flush=True)
        print(f"[END] task={task_id} success=False steps=0 score=0.0 rewards=0.0 error={repr(str(e))}", flush=True)
        return 0.0

    if not isinstance(data, dict) or "ticket_text" not in data:
        print(f"[START] task={task_id} env=ticket_routing_openenv model={MODEL_NAME}", flush=True)
        print(f"[END] task={task_id} success=False steps=0 score=0.0 rewards=0.0 error='invalid reset response'", flush=True)
        return 0.0

    print(f"[START] task={task_id} env=ticket_routing_openenv model={MODEL_NAME}", flush=True)

    ticket_text = data.get("ticket_text", "")
    raw_action = get_action(ticket_text)
    action = normalize_action(raw_action)

    try:
        step_response = requests.post(f"{ENV_URL}/step", json=action, timeout=10)
        result = step_response.json()
    except Exception as e:
        print(f"[STEP] task={task_id} step=1 action={repr(action)} reward=0.0 done=True error={repr(str(e))}", flush=True)
        print(f"[END] task={task_id} success=False steps=1 score=0.0 rewards=0.0", flush=True)
        return 0.0

    reward = float(result.get("reward", 0.0) or 0.0)
    done = bool(result.get("done", True))

    score = reward
    try:
        grade_response = requests.post(
            f"{ENV_URL}/grader",
            json={"task_id": task_id, "action": action},
            timeout=10,
        )
        grade_payload = grade_response.json()
        score = float(grade_payload.get("score", score) or score)
    except Exception:
        pass

    success = score > 0.5

    print(f"[STEP] task={task_id} step=1 action={repr(action)} reward={reward} done={done} error=None", flush=True)
    print(f"[END] task={task_id} success={success} steps=1 score={score} rewards={reward}", flush=True)

    return score


def run():
    tasks = fetch_tasks()

    if not tasks:
        print("No tasks found from /tasks", flush=True)
        return

    graded_tasks = [task for task in tasks if isinstance(task, dict) and has_grader(task)]
    selected_tasks = graded_tasks[:3] if len(graded_tasks) >= 3 else tasks[:3]

    total_score = 0.0

    for task in selected_tasks:
        if not isinstance(task, dict):
            continue
        total_score += run_single_task(task)

    avg_score = total_score / max(len(selected_tasks), 1)
    print(f"[SUMMARY] tasks_run={len(selected_tasks)} avg_score={avg_score}", flush=True)

# ENTRY
if __name__ == "__main__":
    run()