# syntax=docker/dockerfile:1

FROM python:3.11-slim

WORKDIR /submitter

COPY requirements.txt .

COPY run.py .

COPY app.py .

COPY functions /submitter/functions

COPY route /submitter/route

RUN pip3 install -r requirements.txt

EXPOSE 5556

CMD ["python", "run.py"]