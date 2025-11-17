FROM python:3.11-slim

WORKDIR /workspace

COPY . /workspace

RUN apt-get update && apt-get install -y --no-install-recommends build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN chmod +x fixes/setup.sh fixes/run_test.sh && \
    bash fixes/setup.sh

CMD ["bash", "fixes/run_test.sh"]
