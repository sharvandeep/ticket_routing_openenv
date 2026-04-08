FROM python:3.11

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

# Hugging Face sets $PORT (usually 7860). Many validators assume 8000 by default.
# Bind to $PORT when present; otherwise default to 8000.
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
