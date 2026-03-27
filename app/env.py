from app.data import tickets

class TicketEnv:
    def __init__(self):
        self.current_index = 0
        self.current_ticket = None

    # Start new episode
    def reset(self):
        self.current_index = 0
        self.current_ticket = tickets[self.current_index]

        return {
            "ticket_text": self.current_ticket["text"],
            "task_type": self.get_task_type()
        }

    # Current state
    def state(self):
        return {
            "ticket_text": self.current_ticket["text"],
            "task_type": self.get_task_type()
        }

    # Agent takes action
    def step(self, action):
        correct = self.current_ticket

        reward = 0.0

        # Check department
        if action["department"] == correct["department"]:
            reward += 0.4

        # Check priority
        if action["priority"] == correct["priority"]:
            reward += 0.3

        # Check escalation
        if action["escalation"] == correct["escalation"]:
            reward += 0.3

        # Move to next ticket
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