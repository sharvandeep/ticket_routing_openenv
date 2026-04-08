FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

# Hugging Face sets $PORT (usually 7860). Many validators assume 8000 by default.
# Bind to $PORT when present; otherwise default to 8000.
# Avoid shell-based CMD (more reliable on Spaces). `server.app` binds to $PORT (default 8000).
CMD ["python", "-m", "server.app"]
