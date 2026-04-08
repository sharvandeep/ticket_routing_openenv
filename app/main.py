from fastapi import FastAPI, HTTPException
from app.env import TicketEnv
from app.grader import grade
from app.data import tickets

app = FastAPI()
env = TicketEnv()

# Five tasks is safer than the minimum 3
TASKS = [
    {
        "id": "route_easy_chargeback",
        "task_type": "easy",
        "ticket_index": 0,
        "description": "Route a duplicate-charge billing complaint",
    },
    {
        "id": "route_easy_login",
        "task_type": "easy",
        "ticket_index": 1,
        "description": "Route a login/password complaint",
    },
    {
        "id": "route_medium_buffering",
        "task_type": "medium",
        "ticket_index": 3,
        "description": "Route a technical performance complaint",
    },
    {
        "id": "route_medium_email_update",
        "task_type": "medium",
        "ticket_index": 4,
        "description": "Route an email update complaint",
    },
    {
        "id": "route_hard_account_change",
        "task_type": "hard",
        "ticket_index": 2,
        "description": "Route an account settings complaint",
    },
]

TASK_BY_ID = {task["id"]: task for task in TASKS}


@app.get("/")
def home():
    return {"message": "Ticket Routing OpenEnv is running"}


@app.post("/reset")
def reset():
    return env.reset()


@app.get("/state")
def state():
    return env.state()


@app.post("/step")
def step(action: dict):
    observation, reward, done, info = env.step(action)
    return {
        "observation": observation,
        "reward": reward,
        "done": done,
        "info": info,
    }


@app.get("/tasks")
def tasks():
    return {
        "tasks": [
            {
                "id": task["id"],
                "task_type": task["task_type"],
                "description": task["description"],
                "grader": {
                    "endpoint": "/grader",
                    "method": "POST"
                }
            }
            for task in TASKS
        ]
    }



@app.post("/grader")
def grader(payload: dict):
    # Supports:
    # 1) {"task_id": "...", "action": {...}}
    # 2) {"department": "...", "priority": "...", "escalation": "..."}
    task_id = payload.get("task_id")
    action = payload.get("action") if isinstance(payload.get("action"), dict) else payload

    if not isinstance(action, dict):
        raise HTTPException(status_code=400, detail="action must be an object")

    if task_id is None:
        # default to first task if task_id omitted
        task = TASKS[0]
    else:
        task = TASK_BY_ID.get(task_id)
        if task is None:
            raise HTTPException(status_code=400, detail="invalid task_id")

    correct = tickets[task["ticket_index"]]
    score = grade(action, correct)

    return {
        "task_id": task["id"],
        "score": score,
    }


@app.get("/baseline")
def baseline():
    # Baseline evaluates over all tickets deterministically
    total_score = 0.0

    for ticket in tickets:
        action = {
            "department": "technical",
            "priority": "medium",
            "escalation": "no",
        }
        total_score += grade(action, ticket)

    avg_score = total_score / len(tickets) if tickets else 0.0

    return {
        "baseline_score": round(avg_score, 4),
    }