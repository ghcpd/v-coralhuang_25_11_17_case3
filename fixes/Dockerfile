FROM python:3.11-slim
WORKDIR /app
COPY . /app
RUN python -m pip install --upgrade pip && pip install -r fixes/requirements.txt
WORKDIR /app/fixes
ENV FLASK_ENV=test
CMD ["pytest", "-q"]
