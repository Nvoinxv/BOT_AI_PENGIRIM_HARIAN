# =============================================================================
# BEATRICE - PERSONAL AI ASSISTANT BOT
# Production Dockerfile for VPS Deployment
# Pemilik : Kevin
# =============================================================================

# 1. Base Image: Menggunakan Python 3.11 Slim Bookworm yang ringan dan stabil
FROM python:3.11-slim-bookworm

# 2. Metadata Labels
LABEL maintainer="Kevin"
LABEL description="Beatrice Personal AI Assistant Bot (Resend, Finnhub, Gemini, Discord)"
LABEL version="2.0"

# 3. Pengaturan Environment Variables Python & Zona Waktu
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Asia/Jakarta \
    APP_HOME=/app

# 4. Pengaturan Zona Waktu & Sertifikasi Keamanan OS
RUN apt-get update && apt-get install -y --no-install-recommends \
    tzdata \
    ca-certificates \
    curl \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# 5. Buat Pengguna Non-Root (Keamanan Tambahan untuk VPS)
RUN groupadd -r beatrice && useradd -r -g beatrice -d /app -s /sbin/nologin -c "Beatrice Bot User" beatrice

# 6. Atur Direktori Kerja
WORKDIR $APP_HOME

# 7. Salin & Instal Dependensi Python (Memanfaatkan Cache Layer Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# 8. Salin Seluruh Kode Sumber Project
COPY . .

# 9. Buat Folder Logs & Berikan Hak Akses Penuh ke Pengguna Non-Root
RUN mkdir -p $APP_HOME/logs \
    && chown -R beatrice:beatrice $APP_HOME

# 10. Beralih ke Pengguna Non-Root
USER beatrice

# 11. Perintah Utama Menjalankan Bot
CMD ["python", "main.py"]
