from __future__ import annotations

from typing import Optional

from openenv.core.env_server import Action as OpenEnvAction
from openenv.core.env_server import Observation as OpenEnvObservation
from openenv.core.env_server import State as OpenEnvState


class TicketRoutingAction(OpenEnvAction):
    department: str
    priority: str
    escalation: str


class TicketRoutingObservation(OpenEnvObservation):
    ticket_text: Optional[str] = None
    task_type: str


class TicketRoutingState(OpenEnvState):
    current_index: int = 0
    task_id: Optional[str] = None

