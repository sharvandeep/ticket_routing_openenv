---
title: Ticket Routing OpenEnv
emoji: 🤖
colorFrom: blue
colorTo: green
sdk: docker
app_port: 7860
pinned: false
---

# 🚀 Ticket Routing OpenEnv Environment

## 🌍 Overview
This project simulates a real-world customer support ticket routing system, where an AI agent classifies user complaints into the correct department, assigns priority, and decides escalation.

It is built as an OpenEnv-compatible environment to evaluate intelligent agents on realistic enterprise workflows.

---

## 🎯 Motivation
Customer support systems handle thousands of tickets daily. Incorrect routing causes delays and poor user experience.

This environment models that challenge and helps:
- Train AI agents
- Evaluate decision-making
- Benchmark automation systems

---

## ⚙️ Core Features
- Real-world task simulation
- Multi-step environment
- 3 difficulty levels (easy, medium, hard)
- Deterministic grading (0.0–1.0)
- Reward-based learning system
- REST API endpoints
- Hugging Face deployment

---

## 🧠 Task Design
Each ticket must be classified into:

- Department → billing / technical / account / general  
- Priority → low / medium / high  
- Escalation → yes / no  

Difficulty levels:
- Easy → clear tickets  
- Medium → moderate ambiguity  
- Hard → complex interpretation  

---

## 🧮 Reward Function
Reward is calculated per step:

- Correct department → +0.4  
- Correct priority → +0.3  
- Correct escalation → +0.3  

Total reward range: **0.0 to 1.0**

This ensures:
- Partial learning signals
- Continuous feedback
- Realistic evaluation

---

## 🔌 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| /reset   | POST   | Start new episode |
| /step    | POST   | Submit agent action |
| /state   | GET    | Current state |
| /tasks   | GET    | Task metadata |
| /grader  | GET    | Evaluation |
| /baseline| GET    | Baseline score |

---

## 📥 Example

Reset:
POST /reset

Step:
{
  "department": "technical",
  "priority": "high",
  "escalation": "yes"
}

---

## 🤖 Baseline Agent
A baseline agent is provided in `inference.py`.

It uses a hybrid approach:
- Rule-based logic (stable)
- Optional LLM (adaptive)

This ensures:
- Reliability
- Reproducibility
- Compatibility with evaluation

---

## 🧪 Setup (Local)
pip install -r requirements.txt  
uvicorn app.main:app --reload

---

## 🐳 Docker
docker build -t ticket-env .  
docker run -p 7860:7860 ticket-env  

---


## Agent
The inference script uses an LLM (via OpenAI-compatible API) with a fallback rule-based system to ensure stability and consistent performance.

---

## 📊 Evaluation
- Works with OpenEnv validation
- Deterministic grading
- Runs within constraints

---

## 💡 Highlights
- Real-world use case
- Clean design
- Strong reward system
- Fully deployable
- Agent evaluation ready

---

## 🏁 Conclusion
This environment provides a practical benchmark for AI agents in customer support automation, combining real-world relevance with structured evaluation.