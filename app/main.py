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
        "name": "Route: Duplicate charge",
        "task_type": "easy",
        "ticket_index": 0,
        "description": "Route a duplicate-charge billing complaint",
        "difficulty": "easy",
        "max_steps": 1,
        "reward_range": [0.0, 1.0],
        "grader": {"endpoint": "/grader", "method": "POST"},
        "graders": [{"endpoint": "/grader", "method": "POST"}],
    },
    {
        "id": "route_easy_login",
        "name": "Route: Login/password",
        "task_type": "easy",
        "ticket_index": 1,
        "description": "Route a login/password complaint",
        "difficulty": "easy",
        "max_steps": 1,
        "reward_range": [0.0, 1.0],
        "grader": {"endpoint": "/grader", "method": "POST"},
        "graders": [{"endpoint": "/grader", "method": "POST"}],
    },
    {
        "id": "route_medium_buffering",
        "name": "Route: Video buffering",
        "task_type": "medium",
        "ticket_index": 3,
        "description": "Route a technical performance complaint",
        "difficulty": "medium",
        "max_steps": 1,
        "reward_range": [0.0, 1.0],
        "grader": {"endpoint": "/grader", "method": "POST"},
        "graders": [{"endpoint": "/grader", "method": "POST"}],
    },
    {
        "id": "route_medium_email_update",
        "name": "Route: Email update",
        "task_type": "medium",
        "ticket_index": 4,
        "description": "Route an email update complaint",
        "difficulty": "medium",
        "max_steps": 1,
        "reward_range": [0.0, 1.0],
        "grader": {"endpoint": "/grader", "method": "POST"},
        "graders": [{"endpoint": "/grader", "method": "POST"}],
    },
    {
        "id": "route_hard_account_change",
        "name": "Route: Account change",
        "task_type": "hard",
        "ticket_index": 2,
        "description": "Route an account settings complaint",
        "difficulty": "hard",
        "max_steps": 1,
        "reward_range": [0.0, 1.0],
        "grader": {"endpoint": "/grader", "method": "POST"},
        "graders": [{"endpoint": "/grader", "method": "POST"}],
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
                "name": task.get("name", task["id"]),
                "task_type": task["task_type"],
                "difficulty": task.get("difficulty", task["task_type"]),
                "max_steps": task.get("max_steps", 1),
                "reward_range": task.get("reward_range", [0.0, 1.0]),
                "description": task["description"],
                "grader": task.get(
                    "grader",
                    {
                        "endpoint": "/grader",
                        "method": "POST",
                    },
                ),
                "graders": task.get(
                    "graders",
                    [
                        {
                            "endpoint": "/grader",
                            "method": "POST",
                        }
                    ],
                ),
            }
            for task in TASKS
        ]
    }


@app.get("/grader")
def grader_get():
    return {"detail": "Use POST /grader with payload {task_id, action}."}



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