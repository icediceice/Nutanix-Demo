FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY shared_app.py ./
COPY frontend/app.py ./app.py
EXPOSE 8080
CMD ["python", "app.py"]