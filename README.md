# Ticket Routing OpenEnv Environment

## Description
This project simulates a real-world customer support ticket routing system where an AI agent classifies tickets into departments, assigns priority, and decides escalation.

## Features
- Real-world simulation of support systems
- 3 task levels: easy, medium, hard
- Deterministic grading system (0.0–1.0)
- Reward-based learning environment
- REST API endpoints for interaction

## Action Space
- Department: billing, technical, account, general
- Priority: low, medium, high
- Escalation: yes, no

## Observation Space
- ticket_text
- task_type

## Endpoints
- /reset → start new episode
- /step → agent action
- /state → current state
- /tasks → available tasks
- /grader → evaluate performance
- /baseline → baseline agent score

## Setup
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```