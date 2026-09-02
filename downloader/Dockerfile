FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y ffmpeg nodejs npm curl unzip && \
    rm -rf /var/lib/apt/lists/*

# Denoが推奨されたので、新たに追加。
RUN curl -fsSL https://deno.land/install.sh | sh && \
    mv /root/.deno/bin/deno /usr/local/bin/deno

RUN pip install --no-cache-dir yt-dlp fastapi uvicorn python-multipart

WORKDIR /app
COPY app.py .

# --- エントリーポイントスクリプトの追加 ---
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
# ----------------------------------------

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
