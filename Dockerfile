FROM python:3.12-slim

WORKDIR /app

COPY requirements.lock pyproject.toml README.md /app/
COPY src /app/src

RUN pip install --no-cache-dir -r requirements.lock
RUN pip install --no-cache-dir .

RUN apt-get update && apt-get install -y tmux && rm -rf /var/lib/apt/lists/*

EXPOSE 8000

ENTRYPOINT ["python", "-m", "downloader_cli.main"]
