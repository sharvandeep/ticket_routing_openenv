from app.data import tickets

EPSILON = 0.0001

class TicketEnv:
    def __init__(self):
        self.current_index = 0
        self.current_ticket = None
        self.single_task_mode = False

    # Start new episode
    def reset(self, task_index=None):
        if task_index is None:
            self.current_index = 0
            self.single_task_mode = False
        else:
            # Task mode: run exactly one ticket per episode.
            self.current_index = max(0, min(int(task_index), len(tickets) - 1))
            self.single_task_mode = True

        self.current_ticket = tickets[self.current_index]

        return {
            "ticket_text": self.current_ticket["text"],
            "task_type": self.get_task_type()
        }

    # Current state
    def state(self):
        if self.current_ticket is None:
            self.reset()

        return {
            "ticket_text": self.current_ticket["text"],
            "task_type": self.get_task_type()
        }

    # Agent takes action
    def step(self, action):
        if self.current_ticket is None:
            self.reset()

        correct = self.current_ticket

        reward = 0.0

        # Check department
        if action.get("department") == correct["department"]:
            reward += 0.4

        # Check priority
        if action.get("priority") == correct["priority"]:
            reward += 0.3

        # Check escalation
        if action.get("escalation") == correct["escalation"]:
            reward += 0.3

        if reward <= 0.0:
            reward = EPSILON
        elif reward >= 1.0:
            reward = 1.0 - EPSILON

        if self.single_task_mode:
            # In task mode, each task is a one-step episode.
            done = True
        else:
            # Sequential mode keeps compatibility with previous behavior.
            self.current_index += 1
            done = self.current_index >= len(tickets)

            if not done:
                self.current_ticket = tickets[self.current_index]

        return {
            "ticket_text": self.current_ticket["text"] if not done else None,
            "task_type": self.get_task_type()
        }, float(reward), done, {}

    # Difficulty logic (MUST be inside class)
    def get_task_type(self):
        if self.current_index < 2:
            return "easy"
        elif self.current_index < 4:
            return "medium"
        else:
            return "hard"