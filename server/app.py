from fastapi import Request

# Use the canonical OpenEnv server wrapper when available (this is what the
# hackathon validator expects). Fall back to the legacy FastAPI app for local
# development environments where openenv-core isn't installed.
try:
    from openenv.core.env_server import create_fastapi_app  # type: ignore

    from models import TicketRoutingAction, TicketRoutingObservation
    from server.ticket_environment import TicketRoutingEnvironment

    env = TicketRoutingEnvironment()
    app = create_fastapi_app(env, TicketRoutingAction, TicketRoutingObservation)
except Exception:  # pragma: no cover
    from app.main import app  # type: ignore


@app.get("/tasks")
def tasks(request: Request):
    # Keep the existing task metadata + grader compatibility for Phase 2.
    from app.main import TASKS  # local import to avoid circular imports

    tasks_list = [
        {
            "id": task["id"],
            "name": task.get("name", task["id"]),
            "task_type": task["task_type"],
            "difficulty": task.get("difficulty", task["task_type"]),
            "max_steps": task.get("max_steps", 1),
            "reward_range": task.get("reward_range", [0.0, 1.0]),
            "description": task["description"],
            "grader": task.get("grader", {"endpoint": "/grader", "method": "POST"}),
            "graders": task.get(
                "graders",
                [
                    {
                        "endpoint": "/grader",
                        "method": "POST",
                    }
                ],
            ),
            "grader_id": task.get("grader_id", "default"),
            "grader_ids": task.get("grader_ids", ["default"]),
        }
        for task in TASKS
    ]

    if request.query_params.get("format") == "list":
        return tasks_list

    return {"tasks": tasks_list}


@app.post("/grader")
def grader(payload: dict):
    # Delegate to existing deterministic grader
    from app.main import grader as legacy_grader  # local import

    return legacy_grader(payload)


@app.get("/")
def home():
    return {"message": "Ticket Routing OpenEnv is running"}
