# Atlas Nutrition Tracker

[![CI](https://github.com/DevOPsJourneyman/atlas-nutrition-tracker/actions/workflows/ci.yml/badge.svg)](https://github.com/DevOPsJourneyman/atlas-nutrition-tracker/actions/workflows/ci.yml)

A containerised Flask + SQLite meal tracking app built as part of an 88-day DevOps career transition roadmap. Deployed on a self-hosted Proxmox home lab.

## What It Does

- Select today's and tomorrow's meals from the Atlas Nutrition meal plan
- Auto-generates a shopping list by comparing required ingredients against current stock
- Tracks ingredient costs and logs purchases
- Monitors daily macros (calories, protein, fibre) against targets
- Runs on the local network — accessible from any device on the LAN

## Tech Stack

- **Backend:** Python / Flask
- **Database:** SQLite via SQLAlchemy
- **Container:** Docker
- **Orchestration:** Docker Compose
- **Infrastructure:** Ubuntu Server VM on Proxmox home lab

## Docker Concepts Demonstrated

| Concept | Where |
|---|---|
| Layer caching | `COPY requirements.txt` before `COPY . .` in Dockerfile |
| Exec form CMD | `CMD ["python", "app.py"]` for proper signal handling |
| Named volumes | `meal_data:/data` persists SQLite across container restarts |
| Port mapping | `5001:5000` — host port 5001 → container port 5000 |
| Restart policy | `unless-stopped` for production-like reliability |
| `.dockerignore` | Excludes `__pycache__`, `.git`, `.db` from image build context |

## Running Locally

```bash
git clone https://github.com/DevOpsJourneyman/atlas-nutrition-tracker
cd atlas-nutrition-tracker
docker compose up -d
```

App available at `http://localhost:5001`

## Deployment (Home Lab)

Running on `zeus01` (Ubuntu Server 24.04, static IP `192.168.0.24`) — part of a two-node Proxmox cluster (Atlas Lab).

```bash
# SSH into zeus01
ssh zeus@192.168.0.24

# Pull latest and redeploy
cd ~/meal-tracker
git pull
docker compose down
docker compose up -d --build
```

## Part of the DevOps Roadmap

**Week:** 2 — Docker Fundamentals  
**Portfolio goal:** Demonstrate ability to containerise a real application, understand Docker layer caching, volumes, and Compose orchestration.

# Pull and run from Docker Hub
docker pull devopsjourneyman/atlas-nutrition-tracker:latest
docker run -d -p 5001:5000 devopsjourneyman/atlas-nutrition-tracker:latest

Next steps:  add CI/CD pipeline (Week 6).


