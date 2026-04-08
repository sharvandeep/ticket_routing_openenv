from __future__ import annotations

import uuid
from typing import Optional

from app.env import TicketEnv
from openenv.core.env_server import Environment

from models import TicketRoutingAction, TicketRoutingObservation, TicketRoutingState


class TicketRoutingEnvironment(Environment[TicketRoutingAction, TicketRoutingObservation, TicketRoutingState]):
    def __init__(self):
        super().__init__()
        self._env = TicketEnv()
        self._state = TicketRoutingState()

    def reset(
        self,
        seed: Optional[int] = None,
        episode_id: Optional[str] = None,
        **kwargs,
    ) -> TicketRoutingObservation:
        # Reset rubric/transform if used by upstream tooling
        self._reset_rubric()

        obs = self._env.reset()
        self._state = TicketRoutingState(
            episode_id=episode_id or str(uuid.uuid4()),
            step_count=0,
            current_index=self._env.current_index,
            task_id=kwargs.get("task_id"),
        )
        return TicketRoutingObservation(
            ticket_text=obs.get("ticket_text"),
            task_type=obs.get("task_type", "easy"),
            reward=None,
            done=False,
        )

    def step(
        self,
        action: TicketRoutingAction,
        timeout_s: Optional[float] = None,
        **kwargs,
    ) -> TicketRoutingObservation:
        obs, reward, done, _info = self._env.step(
            {
                "department": action.department,
                "priority": action.priority,
                "escalation": action.escalation,
            }
        )

        self._state.step_count += 1
        self._state.current_index = self._env.current_index

        return TicketRoutingObservation(
            ticket_text=obs.get("ticket_text"),
            task_type=obs.get("task_type", "easy"),
            reward=reward,
            done=done,
        )

    @property
    def state(self) -> TicketRoutingState:
        return self._state

