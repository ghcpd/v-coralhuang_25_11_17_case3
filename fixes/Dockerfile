FROM python:3.11-slim
WORKDIR /workspace
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x setup.sh run_test.sh
CMD ["./run_test.sh"]
