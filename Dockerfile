# Dockerfile otimizado

FROM python:3.11-slim

# Definindo o diretório de trabalho
WORKDIR /app

# Copia somente o requirements para aproveitar cache
COPY requirements.txt .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Instala dependências nativas necessárias para o Chromium do Playwright
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 libxkbcommon0 libxcomposite1 libxdamage1 libxrandr2 libxrender1 libgbm1 libpango-1.0-0 libpangocairo-1.0-0 && \
    rm -rf /var/lib/apt/lists/*

# Instala os browsers do Playwright via CLI
RUN pip install playwright && \
    playwright install --with-deps

# Copia todo o código (exceto o que está no .dockerignore)
COPY . .

# (Opcional) Deixa a saída do Python sem buffer, útil para logs em tempo real
ENV PYTHONUNBUFFERED=1

# Comando padrão para iniciar seu bot
CMD ["python", "src/bot.py"]
