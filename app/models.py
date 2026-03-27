from pydantic import BaseModel

# What agent sees
class Observation(BaseModel):
    ticket_text: str
    task_type: str  # easy / medium / hard


# What agent does
class Action(BaseModel):
    department: str
    priority: str
    escalation: str


# What agent gets
class Reward(BaseModel):
    score: float