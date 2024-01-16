FROM python:3.11-slim

EXPOSE 8000

# install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt


ENV SERVER_HOST 0.0.0.0
ENV SERVER_PORT 8000
ENV MONGO_URL mongodb://localhost:3101

# copy source code
COPY /app /app

WORKDIR /app

CMD python main.py