from fastapi import FastAPI
from app.env import TicketEnv
from app.grader import grade
from app.data import tickets

app = FastAPI()

env = TicketEnv()

TASKS = [
    {
        "id": "route_easy_chargeback",
        "task_type": "easy",
        "ticket_index": 0,
        "description": "Route a duplicate-charge billing complaint",
    },
    {
        "id": "route_medium_buffering",
        "task_type": "medium",
        "ticket_index": 3,
        "description": "Route a technical performance complaint",
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
        "info": info
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
                    "method": "POST",
                    "expects": {"task_id": task["id"], "action": "<action_object>"},
                    "score_range": {"min_exclusive": 0.0, "max_exclusive": 1.0},
                },
            }
            for task in TASKS
        ],
        "action_schema": {
            "department": ["billing", "technical", "account", "general"],
            "priority": ["low", "medium", "high"],
            "escalation": ["yes", "no"]
        }
    }


@app.post("/grader")
def grader(payload: dict):
    # Support both payload styles:
    # 1) {"task_id": "...", "action": {...}}
    # 2) {"department": "...", "priority": "...", "escalation": "..."}
    task_id = payload.get("task_id")
    action = payload.get("action") if isinstance(payload.get("action"), dict) else payload

    task = TASK_BY_ID.get(task_id) if task_id else TASKS[0]
    correct = tickets[task["ticket_index"]]
    score = grade(action, correct)

    return {
        "task_id": task["id"],
        "score": score
    }

@app.get("/baseline")
def baseline():
    total_score = 0.0

    for ticket in tickets:
        action = {
            "department": "technical",
            "priority": "medium",
            "escalation": "no"
        }

        score = grade(action, ticket)
        total_score += score

    avg_score = total_score / len(tickets)

    return {
        "baseline_score": avg_score
    }