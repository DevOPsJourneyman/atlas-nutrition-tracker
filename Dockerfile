# ─── Base Image ───────────────────────────────────────────────────────────────
# Every image starts FROM another image. We use python:3.12-slim — the "slim"
# variant strips out docs, man pages, and build tools we don't need.
# This keeps the final image small (~150MB vs ~900MB for the full python image).
# Interview answer: "I chose slim to minimise attack surface and image size."
FROM python:3.12-slim

# ─── Working Directory ────────────────────────────────────────────────────────
# All subsequent commands run from this directory inside the container.
# Think of it as `mkdir -p /app && cd /app` — one instruction.
WORKDIR /app

# ─── Install Dependencies (separate layer for caching) ────────────────────────
# COPY requirements.txt first, then install — this is layer caching in action.
# If requirements.txt hasn't changed, Docker reuses the cached layer and
# skips the pip install entirely. This makes rebuilds much faster.
# Interview answer: "I copy requirements before code so dependency installation
# is cached unless dependencies actually change."
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ─── Copy Application Code ────────────────────────────────────────────────────
# Now copy the app — this layer changes on every code change.
# Because it's AFTER the pip install layer, dependency caching still works.
COPY . .

# ─── Data Directory ───────────────────────────────────────────────────────────
# Create the directory where SQLite will store the database file.
# We'll mount a volume here so data persists when the container restarts.
RUN mkdir -p /data

# ─── Port ─────────────────────────────────────────────────────────────────────
# EXPOSE documents which port the app listens on. It does NOT publish the port.
# Publishing happens at runtime with -p or in docker-compose.yml.
EXPOSE 5000

# ─── Start Command ────────────────────────────────────────────────────────────
# CMD defines the default command when the container starts.
# Using exec form (JSON array) — this makes the process PID 1, which means
# it receives OS signals properly (SIGTERM for graceful shutdown).
# Interview answer: "I use exec form so the process handles signals correctly."
CMD ["python", "app.py"]
