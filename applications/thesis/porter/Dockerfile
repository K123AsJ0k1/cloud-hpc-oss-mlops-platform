# syntax=docker/dockerfile:1

FROM python:3.11-slim-bookworm

WORKDIR /porter

COPY run.py .

COPY app.py .

COPY route /porter/route

COPY functions /porter/functions

COPY requirements.txt .

RUN pip3 install -r requirements.txt

RUN apt-get update

RUN apt-get install -y curl

RUN curl -LO https://storage.googleapis.com/kubernetes-release/release/v1.24.0/bin/linux/amd64/kubectl

RUN chmod +x ./kubectl

RUN mv ./kubectl /usr/local/bin

EXPOSE 5555

CMD ["python", "run.py"]