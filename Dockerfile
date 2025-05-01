# Dockerfile otimizado

FROM python:3.11-slim

# Definindo o diretório de trabalho
WORKDIR /app

# Copia somente o requirements para aproveitar cache
COPY requirements.txt .

# Instala dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o código (exceto o que está no .dockerignore)
COPY . .

# (Opcional) Deixa a saída do Python sem buffer, útil para logs em tempo real
ENV PYTHONUNBUFFERED=1

# Comando padrão para iniciar seu bot
CMD ["python", "src/bot.py"]
