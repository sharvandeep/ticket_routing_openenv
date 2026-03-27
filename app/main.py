from fastapi import FastAPI
from app.env import TicketEnv
from app.grader import grade
from app.data import tickets

app = FastAPI()

env = TicketEnv()

@app.get("/")
def home():
    return {"message": "Ticket Routing OpenEnv is running"}

@app.get("/reset")
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
        "tasks": ["easy", "medium", "hard"],
        "action_schema": {
            "department": ["billing", "technical", "account", "general"],
            "priority": ["low", "medium", "high"],
            "escalation": ["yes", "no"]
        }
    }


@app.post("/grader")
def grader(action: dict):
    # For simplicity, evaluate on first ticket
    correct = tickets[0]
    score = grade(action, correct)

    return {
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