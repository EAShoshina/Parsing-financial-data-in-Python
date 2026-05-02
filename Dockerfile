# Используем Python 3.10
FROM python:3.10-slim

# Рабочая директория внутри контейнера
WORKDIR /app

# Копируем все файлы проекта
COPY . .

# Устанавливаем зависимости
RUN pip install --no-cache-dir fastapi uvicorn pandas scikit-learn requests streamlit plotly joblib

# Открываем порты
EXPOSE 8000 8501

# Запуск FastAPI и Streamlit одновременно
CMD ["bash", "-c", "uvicorn api:app --host 0.0.0.0 --port 8000 & streamlit run streamlit_app.py --server.port 8501 --server.address 0.0.0.0"]
