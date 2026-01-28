# Dockerfile для Koyeb
FROM python:3.11-slim

# Встановлюємо системні залежності
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Створюємо робочу директорію
WORKDIR /app

# Копіюємо requirements та встановлюємо залежності
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копіюємо всі файли проекту
COPY . .

# Відкриваємо порт
EXPOSE 8000

# Запускаємо додаток
CMD ["python", "app.py"]